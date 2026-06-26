"""
Encounter service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Encounter domain.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils import encode_document
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING
from src.services.plan_service import PlanService
import logging

logger = logging.getLogger(__name__)


class EncounterService:
    """
    Service class for Encounter domain operations.

    Handles:
    - RBAC authorization checks (mentor/admin read; owner-or-admin update)
    - MongoDB operations via MongoIO singleton
    - Business logic for Encounter domain
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Authorize an operation for the Encounter domain.

        Users granted either the ``mentor`` or ``admin`` role (per the shared
        ``Config`` role constants) may access encounter data through this
        service. Ownership-sensitive operations (the owner-or-admin ``PATCH``)
        layer an additional check on top of this base authorization via
        :meth:`_check_owner`.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create',
                'update')

        Raises:
            HTTPForbidden: If the caller holds neither the ``mentor`` nor the
                ``admin`` role
        """
        config = Config.get_instance()
        allowed_roles = {config.ROLE_MENTOR, config.ROLE_ADMIN}
        roles = token.get("roles", []) or []
        if not allowed_roles.intersection(roles):
            raise HTTPForbidden(
                "Mentor or admin role required to access encounter data"
            )

    @staticmethod
    def _resolve_caller_profile_id(token):
        """
        Resolve the caller's Profile ``_id`` from the JWT identity.

        Following the domain convention (see ``ProfileService``), the caller's
        Profile is the one whose ``name`` matches the token's ``user_id``. The
        Profile ``_id`` is the mentor id used across the domain (e.g. stored as
        ``Encounter.mentor_id``).

        Args:
            token: Token dictionary with ``user_id`` and roles

        Returns:
            The caller's Profile ``_id``, or ``None`` if no Profile matches.
        """
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        profiles = mongo.get_documents(
            config.PROFILE_COLLECTION_NAME,
            match={"name": token.get("user_id")},
        )
        if not profiles:
            return None
        return profiles[0].get("_id")

    @staticmethod
    def _check_owner(token, encounter):
        """
        Authorize the owning mentor for an ownership-sensitive operation.

        The caller owns the encounter when their resolved Profile ``_id`` equals
        the encounter's ``mentor_id``. Ids are compared as strings to avoid
        ``ObjectId`` vs ``str`` mismatches.

        Args:
            token: Token dictionary with ``user_id`` and roles
            encounter: The target encounter document (already loaded)

        Raises:
            HTTPForbidden: If the caller is not the owning mentor
        """
        caller_profile_id = EncounterService._resolve_caller_profile_id(token)
        mentor_id = encounter.get("mentor_id")
        if caller_profile_id is None or str(caller_profile_id) != str(mentor_id):
            raise HTTPForbidden(
                "Only the owning mentor or an admin may update this encounter"
            )

    @staticmethod
    def _validate_update_data(data):
        """
        Validate update data to prevent security issues.

        Args:
            data: Dictionary of fields to update

        Raises:
            HTTPForbidden: If update data contains restricted fields
        """
        # Prevent updates to _id and system-managed fields
        restricted_fields = ["_id", "created", "saved"]
        for field in restricted_fields:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")

    @staticmethod
    def _build_agenda_from_plan(plan):
        """
        Derive the encounter ``agenda`` from a Plan's checklist.

        ``PlanService`` exposes the Plan list as ``steps`` (stored as
        ``checklist``); each entry becomes an agenda item
        ``{"step": <entry>, "checked": False}``. An empty or absent list
        yields ``[]``.
        """
        steps = plan.get("steps")
        if steps is None:
            steps = plan.get("checklist")
        if not steps:
            return []
        return [{"step": step, "checked": False} for step in steps]

    @staticmethod
    def create_encounter(data, token, breadcrumb):
        """
        Create a new encounter document.

        The request must include ``mentor_id``, ``mentee_id``, and ``plan_id``,
        each a valid 24-hex ObjectId string; otherwise an ``HTTPBadRequest``
        (400) is raised. The referenced Plan is fetched via ``PlanService`` and
        its checklist is used to auto-fill the encounter ``agenda`` (any
        client-supplied ``agenda`` is replaced). A missing Plan surfaces as
        ``HTTPNotFound`` (404).

        Args:
            data: Dictionary containing encounter data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)

        Returns:
            str: The ID of the created encounter document
        """
        try:
            EncounterService._check_permission(token, "create")

            # Required reference ids must be present and valid ObjectId strings
            for field in ("mentor_id", "mentee_id", "plan_id"):
                value = data.get(field)
                if not value:
                    raise HTTPBadRequest(f"{field} is required")
                if not ObjectId.is_valid(value):
                    raise HTTPBadRequest(f"{field} must be a valid ObjectId")

            # Look up the referenced Plan via PlanService (no direct
            # cross-collection access). A missing Plan raises HTTPNotFound.
            plan = PlanService.get_plan(data["plan_id"], token, breadcrumb)

            # Auto-fill agenda from the Plan checklist, overriding any
            # client-supplied agenda.
            data["agenda"] = EncounterService._build_agenda_from_plan(plan)

            # Remove _id if present (MongoDB will generate it)
            if "_id" in data:
                del data["_id"]

            # Encode identifier fields to BSON ObjectId so the collection's
            # $jsonSchema validator accepts the document.
            encode_document(data, ["mentor_id", "mentee_id", "plan_id"], [])

            # Automatically populate required fields: created and saved
            # These are system-managed and should not be provided by the client
            # Use breadcrumb directly as it already has the correct structure
            data["created"] = breadcrumb
            data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            encounter_id = mongo.create_document(config.ENCOUNTER_COLLECTION_NAME, data)
            logger.info(
                f"Created encounter { encounter_id} for user {token.get('user_id')}"
            )
            return encounter_id
        except (HTTPForbidden, HTTPBadRequest, HTTPNotFound):
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating encounter: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create encounter: {error_msg}")

    @staticmethod
    def _normalize_mentee_id(mentee_id):
        """
        Normalize a mentee id for matching against ``Encounter.mentee_id``.

        Encounter documents store ``mentee_id`` as a BSON ``ObjectId`` (the
        mentee's Profile id). Callers may pass either an ``ObjectId`` (e.g. the
        dashboard, which already holds the mentee's ``_id``) or a string id
        (e.g. the detail route). A valid string id is converted so the direct
        Mongo match works; anything else is returned unchanged.
        """
        if isinstance(mentee_id, ObjectId):
            return mentee_id
        try:
            return ObjectId(mentee_id)
        except (InvalidId, TypeError):
            return mentee_id

    @staticmethod
    def get_recent_encounter(mentee_id, token, breadcrumb):
        """
        Return a summary of a mentee's most recent Encounter, or ``None``.

        The most recent encounter is the one with the latest ``date``. The
        summary mirrors the Mentor Dashboard card contract: ``_id``, ``date``,
        ``tldr``, and ``summary``.

        Args:
            mentee_id: The mentee Profile id whose latest encounter is wanted
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for audit/logging

        Returns:
            dict | None: The most recent encounter summary, or ``None`` when the
            mentee has no encounters.
        """
        EncounterService._check_permission(token, "read")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        encounters = mongo.get_documents(
            config.ENCOUNTER_COLLECTION_NAME,
            match={"mentee_id": EncounterService._normalize_mentee_id(mentee_id)},
            sort_by=[("date", DESCENDING)],
        )
        if not encounters:
            return None

        encounter = encounters[0]
        return {
            "_id": encounter["_id"],
            "date": encounter.get("date"),
            "tldr": encounter.get("tldr"),
            "summary": encounter.get("summary"),
        }

    @staticmethod
    def get_encounters_for_mentee(mentee_id, token, breadcrumb):
        """
        Return all of a mentee's Encounter documents, most recent first.

        This is the dedicated per-mentee read used by the Profile detail
        composite. It queries the Encounter collection directly by
        ``mentee_id`` and sorts by ``date`` descending, superseding the interim
        "fetch a page then filter" approach.

        Args:
            mentee_id: The mentee Profile id whose encounters are wanted
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for audit/logging

        Returns:
            list[dict]: The mentee's Encounter documents, most recent first.
        """
        EncounterService._check_permission(token, "read")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        encounters = mongo.get_documents(
            config.ENCOUNTER_COLLECTION_NAME,
            match={"mentee_id": EncounterService._normalize_mentee_id(mentee_id)},
            sort_by=[("date", DESCENDING)],
        )
        logger.info(
            f"Retrieved {len(encounters)} encounters for mentee {mentee_id} "
            f"for user {token.get('user_id')}"
        )
        return encounters

    @staticmethod
    def get_encounter(encounter_id, token, breadcrumb):
        """
        Retrieve a specific encounter document by ID.

        Args:
            encounter_id: The encounter ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The encounter document

        Raises:
            HTTPNotFound: If encounter is not found
        """
        try:
            EncounterService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            encounter = mongo.get_document(
                config.ENCOUNTER_COLLECTION_NAME, encounter_id
            )
            if encounter is None:
                raise HTTPNotFound(f"Encounter { encounter_id} not found")

            logger.info(
                f"Retrieved encounter { encounter_id} for user {token.get('user_id')}"
            )
            return encounter
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error retrieving encounter { encounter_id}: {str(e)}")
            raise HTTPInternalServerError(
                f"Failed to retrieve encounter { encounter_id}"
            )

    @staticmethod
    def update_encounter(encounter_id, data, token, breadcrumb):
        """
        Update a encounter document.

        Args:
            encounter_id: The encounter ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The updated encounter document

        Raises:
            HTTPForbidden: If the caller is not an admin or the owning mentor
            HTTPNotFound: If encounter is not found
        """
        try:
            EncounterService._check_permission(token, "update")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()

            # Load the target encounter first so a missing document yields 404
            # before the ownership check (and to read its mentor_id).
            encounter = mongo.get_document(
                config.ENCOUNTER_COLLECTION_NAME, encounter_id
            )
            if encounter is None:
                raise HTTPNotFound(f"Encounter { encounter_id} not found")

            # Admins may update any encounter; other mentors must own it.
            roles = token.get("roles", []) or []
            if config.ROLE_ADMIN not in roles:
                EncounterService._check_owner(token, encounter)

            EncounterService._validate_update_data(data)

            # Build update data with $set operator (excluding restricted fields)
            restricted_fields = ["_id", "created", "saved"]
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}

            # Automatically update the 'saved' field with current breadcrumb (system-managed)
            # Use breadcrumb directly as it already has the correct structure
            set_data["saved"] = breadcrumb

            updated = mongo.update_document(
                config.ENCOUNTER_COLLECTION_NAME,
                document_id=encounter_id,
                set_data=set_data,
            )

            if updated is None:
                raise HTTPNotFound(f"Encounter { encounter_id} not found")

            logger.info(
                f"Updated encounter { encounter_id} for user {token.get('user_id')}"
            )
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating encounter { encounter_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update encounter { encounter_id}")
