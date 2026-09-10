"""
Mentee service for business logic and RBAC.

Inherits read-only GET from api_utils.services.MenteeService and adds
create-if-missing and update_mentee for Mentor role.
"""

import logging
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils import encode_document
from api_utils.services import MenteeService as SharedMenteeService
from api_utils.services.rbac import is_admin
from bson import ObjectId

logger = logging.getLogger(__name__)

RESTRICTED_FIELDS = ["_id", "profile_id", "created", "saved"]
MENTEE_ID_PROPERTIES = ["_id", "profile_id"]


class MenteeService(SharedMenteeService):
    """
    Service class for Mentee domain operations.

    Inherits base GET from SharedMenteeService and extends:
    - create-if-missing behavior on get_mentee
    - update_mentee
    """

    @classmethod
    def _collection_name(cls, config):
        """Resolve the Mentee collection name from shared config."""
        return config.MENTEE_COLLECTION_NAME

    @classmethod
    def _check_permission(cls, token, operation):
        """
        Inbound RBAC check: create/update requires mentor or admin.
        Read operations delegate to parent.
        """
        config = Config.get_instance()
        roles = token.get("roles", []) or []
        if config.ROLE_ADMIN in roles:
            return
        if operation in ("create", "update"):
            if config.ROLE_MENTOR not in roles:
                raise HTTPForbidden(
                    "Mentor or admin role required to access mentee data"
                )
        else:
            super()._check_permission(token, operation)

    @classmethod
    def _require_mentee_visible(cls, document, token, profile_id):
        """Check outbound RBAC visibility for a mentee document using _id or profile_id."""
        if document is None:
            raise HTTPNotFound(f"Mentee for profile {profile_id} not found")
        if is_admin(token):
            return document
        if cls._is_archived(document):
            raise HTTPNotFound(f"Mentee for profile {profile_id} not found")

        caller_profile_id = token.get("profile_id")
        doc_profile_id = document.get("_id") or document.get("profile_id")
        if isinstance(doc_profile_id, dict) and "$oid" in doc_profile_id:
            doc_profile_id = doc_profile_id["$oid"]
        if (
            caller_profile_id
            and doc_profile_id
            and str(caller_profile_id).lower() == str(doc_profile_id).lower()
        ):
            return document

        if cls._mentor_of_profile(doc_profile_id or profile_id, token):
            return document

        raise HTTPNotFound(f"Mentee for profile {profile_id} not found")

    ALLOWED_UPDATE_FIELDS = {"summary", "notes", "status"}

    @classmethod
    def _validate_update_data(cls, data):
        """Reject updates targeting system-managed or disallowed fields."""
        for field in RESTRICTED_FIELDS:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")
        for field in data:
            if field not in cls.ALLOWED_UPDATE_FIELDS:
                raise HTTPForbidden(f"Cannot update {field} field")

    @classmethod
    def _default_document(cls, profile_id, breadcrumb):
        """Build a schema-valid default Mentee document for a Profile."""
        doc = {
            "_id": profile_id,
            "status": "active",
            "summary": "",
            "notes": "",
            "created": breadcrumb,
            "saved": breadcrumb,
        }
        encode_document(doc, MENTEE_ID_PROPERTIES, [])
        return doc

    @classmethod
    def get_mentee(cls, profile_id, token, breadcrumb):
        """
        Retrieve mentee document, creating only when none exists.

        Shared parent 404 covers both missing and hidden/archived/out-of-scope
        rows. Create-if-missing must apply only when no document exists;
        otherwise re-raise 404 so hidden ids are not leaked via a new row.
        """
        try:
            cls._check_permission(token, "read")
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection_name = cls._collection_name(config)

            match = {
                "$or": [
                    {"_id": profile_id},
                    {"profile_id": profile_id},
                ]
            }
            try:
                encode_document(match, MENTEE_ID_PROPERTIES, [])
            except ValueError:
                raise HTTPBadRequest(f"Invalid profile_id: {profile_id}")

            existing = mongo.get_documents(collection_name, match=match)
            if existing:
                # Existing row: shared visibility (404 if hidden). Never create.
                return cls._require_mentee_visible(existing[0], token, profile_id)

            cls._check_permission(token, "create")
            document = cls._default_document(profile_id, breadcrumb)
            mentee_id = mongo.create_document(collection_name, document)
            created_doc = mongo.get_document(collection_name, mentee_id)
            logger.info(
                f"Created default mentee for profile {profile_id} by {token.get('user_id')}"
            )
            return created_doc
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error retrieving mentee for profile {profile_id}: {str(e)}")
            raise HTTPInternalServerError(
                f"Failed to retrieve mentee for profile {profile_id}"
            )

    @classmethod
    def update_mentee(cls, mentee_id, data, token, breadcrumb):
        """Update an existing mentee document."""
        try:
            cls._check_permission(token, "update")
            cls._validate_update_data(data)
            match_id = {"_id": mentee_id}
            match_profile = {"profile_id": mentee_id}
            try:
                encode_document(match_id, MENTEE_ID_PROPERTIES, [])
                encode_document(match_profile, MENTEE_ID_PROPERTIES, [])
            except ValueError:
                raise HTTPBadRequest(f"Invalid mentee_id: {mentee_id}")

            set_data = {k: v for k, v in data.items() if k not in RESTRICTED_FIELDS}
            set_data["saved"] = breadcrumb
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection_name = cls._collection_name(config)
            updated = mongo.update_document(
                collection_name,
                match=match_id,
                set_data=set_data,
            )
            if updated is None:
                updated = mongo.update_document(
                    collection_name,
                    match=match_profile,
                    set_data=set_data,
                )
            if updated is None:
                raise HTTPNotFound(f"Mentee {mentee_id} not found")
            logger.info(f"Updated mentee {mentee_id} for user {token.get('user_id')}")
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating mentee {mentee_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update mentee {mentee_id}")
