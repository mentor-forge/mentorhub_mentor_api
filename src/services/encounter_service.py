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
from src.services.plan_service import PlanService

try:
    from api_utils.services import EncounterService as SharedEncounterService
except ImportError:  # pragma: no cover

    class SharedEncounterService:
        @classmethod
        def _check_permission(cls, token, operation, breadcrumb):
            pass

        @classmethod
        def get_encounter(cls, encounter_id, token, breadcrumb):
            pass

        @classmethod
        def get_encounters_for_mentee(
            cls, mentee_id, token, breadcrumb, offset=None, size=None
        ):
            pass

        @classmethod
        def get_recent_encounter(cls, mentee_id, token, breadcrumb):
            pass


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
    def _validate_update_data(cls, data):
        """Reject updates targeting system-managed fields."""
        restricted_fields = ["_id", "created", "saved"]
        for field in restricted_fields:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")

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
            cls._validate_update_data(data)
            restricted_fields = ["_id", "created", "saved"]
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}
            set_data["saved"] = breadcrumb
            updated = mongo.update_document(
                config.ENCOUNTER_COLLECTION_NAME,
                document_id=encounter_id,
                set_data=set_data,
            )
            if updated is None:
                raise HTTPNotFound(f"Encounter {encounter_id} not found")
            logger.info(
                f"Updated encounter {encounter_id} for user {token.get('user_id')}"
            )
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating encounter {encounter_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update encounter {encounter_id}")
