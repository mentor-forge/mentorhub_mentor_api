"""
Mentee service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for the Mentee domain. A Mentee
document holds the mentor's notes about a single mentee, keyed by the mentee's
Profile id. The read endpoint follows a "create-if-missing" pattern so the UI
always receives a valid document for a known Profile.

Per the API standards (separation of concerns), this service contains business
logic only. It raises the appropriate domain exceptions (e.g. HTTPForbidden,
HTTPNotFound); the route layer's ``@handle_route_exceptions`` wrapper is
responsible for translating those, and any unexpected error, into HTTP
responses.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from bson import ObjectId
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)

# Fields the client may never set/overwrite directly (system-managed).
RESTRICTED_FIELDS = ["_id", "created", "saved"]


class MenteeService:
    """
    Service class for Mentee domain operations.

    Handles:
    - RBAC authorization checks (requires the ``mentor`` or ``admin`` role)
    - MongoDB operations via MongoIO singleton
    - Read-with-create-if-missing and update of the mentee-notes document
    """

    @staticmethod
    def _collection_name(config):
        """Resolve the Mentee collection name from shared config."""
        return config.MENTEE_COLLECTION_NAME

    @staticmethod
    def _check_permission(token, operation):
        """
        Authorize an operation for the Mentee domain.

        Users granted either the ``mentor`` or ``admin`` role (per the shared
        ``Config`` role constants) may access mentee data through this service.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'update')

        Raises:
            HTTPForbidden: If the caller holds neither the ``mentor`` nor the
                ``admin`` role
        """
        config = Config.get_instance()
        allowed_roles = {config.ROLE_MENTOR, config.ROLE_ADMIN}
        roles = token.get("roles", []) or []
        if not allowed_roles.intersection(roles):
            raise HTTPForbidden("Mentor or admin role required to access mentee data")

    @staticmethod
    def _to_object_id(value, label):
        """
        Convert a string id to a BSON ``ObjectId``.

        Args:
            value: The id value to convert
            label: Human-readable field name used in error messages

        Returns:
            ObjectId: The converted id

        Raises:
            HTTPBadRequest: If the value is not a valid ObjectId
        """
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            raise HTTPBadRequest(f"Invalid {label}: {value}")

    @staticmethod
    def _validate_update_data(data):
        """
        Reject updates that target system-managed fields.

        Args:
            data: Dictionary of fields to update

        Raises:
            HTTPForbidden: If update data contains restricted fields
        """
        for field in RESTRICTED_FIELDS:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")

    @staticmethod
    def _default_document(profile_object_id, breadcrumb):
        """
        Build a schema-valid default Mentee document for a Profile.

        The shape satisfies the Mentee JSON schema (``additionalProperties:
        false``): ``profile_id`` is an ``ObjectId``, ``status`` defaults to
        ``active``, the optional text fields default to empty strings, and the
        ``created``/``saved`` breadcrumbs come from the request. The optional
        ``name``, ``next_appointment``, and ``schedule`` fields are omitted
        rather than seeded with values that would fail pattern/format
        validation.
        """
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

    @staticmethod
    def get_mentee(profile_id, token, breadcrumb):
        """
        Retrieve the mentee-notes document for a Profile, creating it if needed.

        Looks up the Mentee document by ``profile_id``. If none exists yet, a
        default document is created and returned so callers always receive a
        valid document.

        Args:
            profile_id: The mentee Profile id (string ObjectId)
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for audit/logging

        Returns:
            dict: The existing or newly created Mentee document

        Raises:
            HTTPBadRequest: If profile_id is not a valid ObjectId
            HTTPForbidden: If the caller does not hold the ``mentor`` role
        """
        try:
            MenteeService._check_permission(token, "read")
            profile_object_id = MenteeService._to_object_id(profile_id, "profile_id")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection_name = MenteeService._collection_name(config)

            existing = mongo.get_documents(
                collection_name, match={"profile_id": profile_object_id}
            )
            if existing:
                logger.info(
                    f"Retrieved mentee for profile {profile_id} "
                    f"for user {token.get('user_id')}"
                )
                return existing[0]

            # Create-if-missing: persist a default document and return it.
            document = MenteeService._default_document(profile_object_id, breadcrumb)
            mentee_id = mongo.create_document(collection_name, document)
            created = mongo.get_document(collection_name, mentee_id)
            logger.info(
                f"Created default mentee {mentee_id} for profile {profile_id} "
                f"for user {token.get('user_id')}"
            )
            return created
        except (HTTPBadRequest, HTTPForbidden):
            raise
        except Exception as e:
            logger.error(f"Error retrieving mentee for profile {profile_id}: {str(e)}")
            raise HTTPInternalServerError(
                f"Failed to retrieve mentee for profile {profile_id}"
            )

    @staticmethod
    def update_mentee(mentee_id, data, token, breadcrumb):
        """
        Update a Mentee notes document.

        Args:
            mentee_id: The Mentee document id (string ObjectId)
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for audit/logging

        Returns:
            dict: The updated Mentee document

        Raises:
            HTTPBadRequest: If mentee_id is not a valid ObjectId
            HTTPForbidden: If the caller lacks the ``mentor`` role or the update
                targets a restricted field
            HTTPNotFound: If the Mentee document does not exist
        """
        try:
            MenteeService._check_permission(token, "update")
            MenteeService._validate_update_data(data)
            mentee_object_id = MenteeService._to_object_id(mentee_id, "mentee_id")

            # Build $set data, excluding restricted fields, and stamp 'saved'.
            set_data = {k: v for k, v in data.items() if k not in RESTRICTED_FIELDS}
            set_data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection_name = MenteeService._collection_name(config)
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
