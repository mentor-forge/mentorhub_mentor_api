"""
Encounter service for business logic and RBAC.

Inherits shared GET helpers from api_utils.services.EncounterService.
Keeps mentor-local write CRUD (create and update) with owner-or-admin RBAC.
"""

import logging
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
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
        steps = plan.get("steps")
        if steps is None:
            steps = plan.get("checklist")
        if not steps:
            return []
        return [{"step": step, "checked": False} for step in steps]

    @classmethod
    def _check_permission_write(cls, token, operation, breadcrumb, encounter=None):
        """
        Inbound write RBAC check.
        Create requires mentor or admin.
        Update requires owning mentor (encounter.mentor_id equals caller profile_id) or admin.
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
