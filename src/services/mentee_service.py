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
from bson import ObjectId
from bson.errors import InvalidId

try:
    from api_utils.services import MenteeService as SharedMenteeService
except ImportError:  # pragma: no cover

    class SharedMenteeService:
        @classmethod
        def _check_permission(cls, token, operation):
            pass

        @classmethod
        def _collection_name(cls, config):
            return config.MENTEE_COLLECTION_NAME

        @classmethod
        def _to_object_id(cls, value, label):
            try:
                return ObjectId(value)
            except (InvalidId, TypeError):
                raise HTTPBadRequest(f"Invalid {label}: {value}")

        @classmethod
        def get_mentee(cls, profile_id, token, breadcrumb):
            profile_object_id = cls._to_object_id(profile_id, "profile_id")
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection_name = cls._collection_name(config)
            existing = mongo.get_documents(
                collection_name, match={"profile_id": profile_object_id}
            )
            if existing:
                return existing[0]
            raise HTTPNotFound(f"Mentee for profile {profile_id} not found")


logger = logging.getLogger(__name__)

RESTRICTED_FIELDS = ["_id", "created", "saved"]


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
    def _to_object_id(cls, value, label):
        """Convert a string id to a BSON ObjectId."""
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            raise HTTPBadRequest(f"Invalid {label}: {value}")

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
            if hasattr(super(), "_check_permission"):
                super()._check_permission(token, operation)

    @classmethod
    def _validate_update_data(cls, data):
        """Reject updates targeting system-managed fields."""
        for field in RESTRICTED_FIELDS:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")

    @classmethod
    def _default_document(cls, profile_object_id, breadcrumb):
        """Build a schema-valid default Mentee document for a Profile."""
        return {
            "profile_id": profile_object_id,
            "status": "active",
            "description": "",
            "focus": "",
            "homework": "",
            "notes": "",
            "created": breadcrumb,
            "saved": breadcrumb,
        }

    @classmethod
    def get_mentee(cls, profile_id, token, breadcrumb):
        """Retrieve mentee document, creating if missing for mentor/admin."""
        try:
            try:
                return super().get_mentee(profile_id, token, breadcrumb)
            except HTTPNotFound:
                cls._check_permission(token, "create")
                profile_object_id = cls._to_object_id(profile_id, "profile_id")
                mongo = MongoIO.get_instance()
                config = Config.get_instance()
                collection_name = cls._collection_name(config)
                document = cls._default_document(profile_object_id, breadcrumb)
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
            mentee_object_id = cls._to_object_id(mentee_id, "mentee_id")
            set_data = {k: v for k, v in data.items() if k not in RESTRICTED_FIELDS}
            set_data["saved"] = breadcrumb
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection_name = cls._collection_name(config)
            updated = mongo.update_document(
                collection_name,
                match={"_id": mentee_object_id},
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
