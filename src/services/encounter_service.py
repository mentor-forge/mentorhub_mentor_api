"""
Encounter service for business logic and RBAC.

Inherits shared GET helpers from api_utils.services.EncounterService.
Keeps mentor-local write CRUD (create and update) with owner-or-admin RBAC.
"""

import logging
from datetime import datetime, timedelta, timezone
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils import encode_document
from api_utils.services import EncounterService as SharedEncounterService
from src.services.plan_service import PlanService

logger = logging.getLogger(__name__)


class EncounterService(SharedEncounterService):
    """
    Service class for Encounter domain operations.

    Inherits GET methods from SharedEncounterService:
    - get_encounter
    - get_encounters_for_mentee
    - get_recent_encounter

    Implements local write CRUD:
    - create_encounter
    - update_encounter
    """

    @classmethod
    def _enrich_encounter(cls, encounter, mongo=None, config=None):
        """Enrich an encounter document with mentor_name and mentee_name from Profile display_name."""
        if not encounter or not isinstance(encounter, dict):
            return encounter
        mongo = mongo or MongoIO.get_instance()
        config = config or Config.get_instance()

        mentor_id = encounter.get("mentor_id")
        if mentor_id:
            mentor = mongo.get_document(config.PROFILE_COLLECTION_NAME, str(mentor_id))
            encounter["mentor_name"] = mentor.get("display_name") if mentor else None
        else:
            encounter["mentor_name"] = None

        mentee_id = encounter.get("mentee_id")
        if mentee_id:
            mentee = mongo.get_document(config.PROFILE_COLLECTION_NAME, str(mentee_id))
            encounter["mentee_name"] = mentee.get("display_name") if mentee else None
        else:
            encounter["mentee_name"] = None

        return encounter

    @classmethod
    def _enrich_encounters(cls, encounters, mongo=None, config=None):
        """Enrich a list of encounter documents with mentor_name and mentee_name."""
        if not encounters:
            return encounters
        mongo = mongo or MongoIO.get_instance()
        config = config or Config.get_instance()
        cache = {}

        def get_profile_name(pid):
            if not pid:
                return None
            key = str(pid)
            if key in cache:
                return cache[key]
            prof = mongo.get_document(config.PROFILE_COLLECTION_NAME, key)
            name = prof.get("display_name") if prof else None
            cache[key] = name
            return name

        for enc in encounters:
            if isinstance(enc, dict):
                enc["mentor_name"] = get_profile_name(enc.get("mentor_id"))
                enc["mentee_name"] = get_profile_name(enc.get("mentee_id"))
        return encounters

    @classmethod
    def get_encounter(cls, encounter_id, token, breadcrumb):
        """Retrieve a specific encounter document by ID and enrich with names."""
        encounter = super().get_encounter(encounter_id, token, breadcrumb)
        return cls._enrich_encounter(encounter)

    @classmethod
    def get_encounters_for_mentee(cls, mentee_id, token, breadcrumb, offset=0, size=20):
        """Retrieve encounters for a mentee and enrich with names."""
        encounters = super().get_encounters_for_mentee(
            mentee_id, token, breadcrumb, offset=offset, size=size
        )
        return cls._enrich_encounters(encounters)

    @classmethod
    def get_recent_encounter(cls, mentee_id, token, breadcrumb):
        """Retrieve the most recent encounter for a mentee and enrich with names."""
        encounter = super().get_recent_encounter(mentee_id, token, breadcrumb)
        return cls._enrich_encounter(encounter)

    ALLOWED_UPDATE_FIELDS = {"agenda", "transcript", "summary", "tldr"}

    @classmethod
    def _validate_update_data(cls, data):
        """Allow only agenda, transcript, summary, and tldr updates."""
        if not data:
            return
        for field in data:
            if field not in cls.ALLOWED_UPDATE_FIELDS:
                raise HTTPForbidden(f"Cannot update {field} field")
        if "agenda" in data:
            agenda = data["agenda"]
            if not isinstance(agenda, list):
                raise HTTPForbidden("Field 'agenda' must be a list")
            for item in agenda:
                if not isinstance(item, dict) or "checked" not in item:
                    raise HTTPForbidden(
                        "Each item in 'agenda' must be an object with 'checked'"
                    )

    @classmethod
    def _build_agenda_from_plan(cls, plan):
        """Derive the encounter agenda from a Plan's steps or checklist."""
        if not plan:
            return []
        steps = plan.get("steps")
        if steps is None:
            steps = plan.get("checklist")
        if not steps:
            return []
        return [{"step": step, "checked": False} for step in steps]

    @classmethod
    def _check_permission_write(
        cls, token, operation, breadcrumb, encounter=None, mentor_id=None
    ):
        """
        Inbound write RBAC check.
        Create requires mentor or admin.
        Update requires owning mentor (encounter.mentor_id equals caller profile_id) or admin.
        Schedule requires assigned mentor (mentor_id equals caller profile_id) or admin.
        """
        from src.services.profile_service import ProfileService

        config = Config.get_instance()
        roles = token.get("roles", []) or []
        if config.ROLE_ADMIN in roles:
            return
        if config.ROLE_MENTOR not in roles:
            raise HTTPForbidden(
                "Mentor or admin role required to access encounter data"
            )
        if encounter is not None:
            profile = ProfileService.get_profile_by_token(token, breadcrumb)
            caller_profile_id = profile.get("_id") if profile else None
            if caller_profile_id is None or str(caller_profile_id) != str(
                encounter.get("mentor_id")
            ):
                raise HTTPForbidden(
                    "Only the owning mentor or an admin may update this encounter"
                )
        if mentor_id is not None:
            profile = ProfileService.get_profile_by_token(token, breadcrumb)
            caller_profile_id = profile.get("_id") if profile else None
            if caller_profile_id is None or str(caller_profile_id) != str(mentor_id):
                raise HTTPForbidden(
                    "Only the assigned mentor or an admin may schedule encounters for this mentor"
                )

    @classmethod
    def schedule_encounters(cls, data, token, breadcrumb):
        """Schedule multiple recurring encounters with plan agenda auto-fill and appointment calculations."""
        try:
            config = Config.get_instance()
            roles = token.get("roles", []) or []
            if config.ROLE_ADMIN not in roles and config.ROLE_MENTOR not in roles:
                raise HTTPForbidden(
                    "Mentor or admin role required to access encounter data"
                )

            if not isinstance(data, dict):
                raise HTTPBadRequest("Request payload must be a JSON object")

            required_fields = [
                "mentor_id",
                "mentee_id",
                "plan_id",
                "start_date",
                "time_of_day",
                "count",
            ]
            for field in required_fields:
                if not data.get(field):
                    raise HTTPBadRequest(f"Missing required field: '{field}'")

            cls._check_permission_write(
                token, "schedule", breadcrumb, mentor_id=data["mentor_id"]
            )

            start_date_str = str(data["start_date"])
            try:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                raise HTTPBadRequest(
                    f"Invalid start_date '{start_date_str}', expected YYYY-MM-DD"
                )

            time_of_day_str = str(data["time_of_day"])
            time_parts = time_of_day_str.split(":")
            if len(time_parts) not in (2, 3):
                raise HTTPBadRequest(
                    f"Invalid time_of_day '{time_of_day_str}', expected HH:MM or HH:MM:SS"
                )
            try:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2]) if len(time_parts) == 3 else 0
                if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                    raise ValueError
            except (ValueError, TypeError):
                raise HTTPBadRequest(f"Invalid time_of_day '{time_of_day_str}'")

            dow = data.get("day_of_week")
            if dow is None:
                dow = data.get("day-of-week")

            if dow is not None:
                try:
                    dow = int(dow)
                    if not (0 <= dow <= 6):
                        raise ValueError
                except (ValueError, TypeError):
                    raise HTTPBadRequest(
                        f"Invalid day_of_week '{dow}', must be integer 0-6"
                    )
            else:
                dow = (start_dt.weekday() + 1) % 7

            target_python_weekday = (dow - 1) % 7
            days_ahead = (target_python_weekday - start_dt.weekday()) % 7
            first_date = start_dt + timedelta(days=days_ahead)

            recurrence_days = data.get("recurrence_days", 7)
            try:
                recurrence_days = int(recurrence_days)
                if recurrence_days < 1:
                    raise ValueError
            except (ValueError, TypeError):
                raise HTTPBadRequest(
                    f"Invalid recurrence_days '{recurrence_days}', must be integer >= 1"
                )

            try:
                count = int(data["count"])
                if count < 1 or count > 100:
                    raise ValueError
            except (ValueError, TypeError):
                raise HTTPBadRequest("Invalid count, must be integer >= 1")

            plan = PlanService.get_plan(data["plan_id"], token, breadcrumb)
            agenda = cls._build_agenda_from_plan(plan)

            mongo = MongoIO.get_instance()
            created_encounters = []
            for i in range(count):
                encounter_date = first_date + timedelta(days=i * recurrence_days)
                from_dt = datetime(
                    encounter_date.year,
                    encounter_date.month,
                    encounter_date.day,
                    hour,
                    minute,
                    second,
                    tzinfo=timezone.utc,
                )
                to_dt = from_dt + timedelta(hours=1)
                doc = {
                    "mentor_id": data["mentor_id"],
                    "mentee_id": data["mentee_id"],
                    "plan_id": data["plan_id"],
                    "status": "scheduled",
                    "appointment": {
                        "from": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    },
                    "agenda": [dict(item) for item in agenda],
                    "created": breadcrumb,
                    "saved": breadcrumb,
                }
                encode_document(doc, ["mentor_id", "mentee_id", "plan_id"], [])
                encounter_id = mongo.create_document(
                    config.ENCOUNTER_COLLECTION_NAME, doc
                )
                created_doc = mongo.get_document(
                    config.ENCOUNTER_COLLECTION_NAME, encounter_id
                )
                if created_doc is None:
                    created_doc = dict(doc)
                    created_doc["_id"] = encounter_id
                created_encounters.append(created_doc)

            enriched = cls._enrich_encounters(created_encounters, mongo, config)
            logger.info(
                f"Scheduled {len(enriched)} encounters for user {token.get('user_id')}"
            )
            return enriched
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error scheduling encounters: {str(e)}")
            raise HTTPInternalServerError(f"Failed to schedule encounters: {e}")

    @classmethod
    def create_encounter(cls, data, token, breadcrumb):
        """Create a new encounter document with auto-filled agenda from plan."""
        try:
            cls._check_permission_write(token, "create", breadcrumb)
            plan = PlanService.get_plan(data["plan_id"], token, breadcrumb)
            data["agenda"] = cls._build_agenda_from_plan(plan)
            if "_id" in data:
                del data["_id"]
            encode_document(data, ["mentor_id", "mentee_id", "plan_id"], [])
            data["created"] = breadcrumb
            data["saved"] = breadcrumb
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            encounter_id = mongo.create_document(config.ENCOUNTER_COLLECTION_NAME, data)
            logger.info(
                f"Created encounter {encounter_id} for user {token.get('user_id')}"
            )
            return encounter_id
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error creating encounter: {str(e)}")
            raise HTTPInternalServerError(f"Failed to create encounter: {e}")

    @classmethod
    def update_encounter(cls, encounter_id, data, token, breadcrumb):
        """Update an encounter document with ownership / admin check."""
        try:
            cls._check_permission_write(token, "update", breadcrumb)
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            encounter = mongo.get_document(
                config.ENCOUNTER_COLLECTION_NAME, encounter_id
            )
            if encounter is None:
                raise HTTPNotFound(f"Encounter {encounter_id} not found")
            cls._check_permission_write(
                token, "update", breadcrumb, encounter=encounter
            )
            if encounter.get("status") != "active":
                raise HTTPForbidden(
                    f"Cannot update encounter: status must be 'active', got '{encounter.get('status')}'"
                )
            cls._validate_update_data(data)
            set_data = {k: v for k, v in data.items() if k in cls.ALLOWED_UPDATE_FIELDS}
            set_data["saved"] = breadcrumb
            updated = mongo.update_document(
                config.ENCOUNTER_COLLECTION_NAME,
                document_id=encounter_id,
                set_data=set_data,
            )
            if updated is None:
                raise HTTPNotFound(f"Encounter {encounter_id} not found")
            updated = cls._enrich_encounter(updated, mongo, config)
            logger.info(
                f"Updated encounter {encounter_id} for user {token.get('user_id')}"
            )
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating encounter {encounter_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update encounter {encounter_id}")

    @classmethod
    def _verify_and_decrement_subscription(cls, mentee_id, mongo, config, breadcrumb):
        """Verify mentee has customer with active subscription and positive balance, then decrement balance."""
        if not mentee_id:
            raise HTTPForbidden("Mentee has no associated customer")

        profile = mongo.get_document(config.PROFILE_COLLECTION_NAME, str(mentee_id))
        if not profile or not profile.get("customer_id"):
            raise HTTPForbidden("Mentee has no associated customer")

        customer_id = profile["customer_id"]
        customer_collection = getattr(config, "CUSTOMER_COLLECTION_NAME", "Customer")
        customer = mongo.get_document(customer_collection, str(customer_id))
        if not customer:
            raise HTTPForbidden(f"Customer {customer_id} not found")

        subscriptions = customer.get("subscriptions", [])
        qualifying_sub = None
        for sub in subscriptions:
            if (
                sub.get("status") == "active"
                and sub.get("free_encounters_remaining", 0) > 0
            ):
                qualifying_sub = sub
                break

        if qualifying_sub is None:
            raise HTTPForbidden("Insufficient subscription balance to start encounter")

        qualifying_sub["free_encounters_remaining"] = (
            qualifying_sub.get("free_encounters_remaining", 0) - 1
        )

        mongo.update_document(
            customer_collection,
            document_id=str(customer_id),
            set_data={"subscriptions": subscriptions, "saved": breadcrumb},
        )

    @classmethod
    def start_encounter(cls, encounter_id, token, breadcrumb):
        """Start an encounter: verify scheduled status, decrement customer subscription, set active, log event."""
        try:
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            encounter = mongo.get_document(
                config.ENCOUNTER_COLLECTION_NAME, encounter_id
            )
            if encounter is None:
                raise HTTPNotFound(f"Encounter {encounter_id} not found")

            cls._check_permission_write(
                token, "update", breadcrumb, encounter=encounter
            )

            current_status = encounter.get("status")
            if current_status != "scheduled":
                raise HTTPForbidden(
                    f"Cannot start encounter: status is '{current_status}', expected 'scheduled'"
                )

            cls._verify_and_decrement_subscription(
                encounter.get("mentee_id"), mongo, config, breadcrumb
            )

            updated = mongo.update_document(
                config.ENCOUNTER_COLLECTION_NAME,
                document_id=encounter_id,
                set_data={"status": "active", "saved": breadcrumb},
            )
            if updated is None:
                raise HTTPNotFound(f"Encounter {encounter_id} not found")

            from src.services.event_service import EventService

            EventService.create_event(
                {
                    "type": getattr(config, "EVENT_TYPE_ENCOUNTER", "encounter"),
                    "context": {
                        "encounter_id": str(encounter_id),
                        "mentor_id": str(encounter.get("mentor_id")),
                        "mentee_id": str(encounter.get("mentee_id")),
                    },
                },
                token,
                breadcrumb,
            )

            updated = cls._enrich_encounter(updated, mongo, config)
            logger.info(
                f"Started encounter {encounter_id} for user {token.get('user_id')}"
            )
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error starting encounter {encounter_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to start encounter {encounter_id}")

    @classmethod
    def finish_encounter(cls, encounter_id, token, breadcrumb):
        """Finish an encounter: verify active status, set status complete."""
        try:
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            encounter = mongo.get_document(
                config.ENCOUNTER_COLLECTION_NAME, encounter_id
            )
            if encounter is None:
                raise HTTPNotFound(f"Encounter {encounter_id} not found")

            cls._check_permission_write(
                token, "update", breadcrumb, encounter=encounter
            )

            current_status = encounter.get("status")
            if current_status != "active":
                raise HTTPForbidden(
                    f"Cannot finish encounter: status is '{current_status}', expected 'active'"
                )

            updated = mongo.update_document(
                config.ENCOUNTER_COLLECTION_NAME,
                document_id=encounter_id,
                set_data={"status": "complete", "saved": breadcrumb},
            )
            if updated is None:
                raise HTTPNotFound(f"Encounter {encounter_id} not found")

            updated = cls._enrich_encounter(updated, mongo, config)
            logger.info(
                f"Finished encounter {encounter_id} for user {token.get('user_id')}"
            )
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error finishing encounter {encounter_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to finish encounter {encounter_id}")
