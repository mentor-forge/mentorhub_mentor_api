"""
Event service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Event domain.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils import encode_document
from pymongo import ASCENDING
import logging

logger = logging.getLogger(__name__)

# Identifier fields stored as BSON ObjectId per the Event dictionary
# (the schema validator rejects string ids). encode_document recurses into
# nested objects, so this also covers context.profile_id.
ID_PROPERTIES = ["_id", "profile_id"]
DATE_PROPERTIES = []


class EventService:
    """
    Service class for Event domain operations.

    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Event domain
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create')

        Raises:
            HTTPForbidden: If user doesn't have required permission

        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).

        Example RBAC implementation:
            if operation == 'create':
                # Event requires staff or admin role
                if not any(role in token.get('roles', []) for role in ['staff', 'admin']):
                    raise HTTPForbidden("Staff or admin role required to create event documents")
            elif operation == 'read':
                # Read requires any authenticated user (no additional check needed)
                pass
        """
        pass

    @staticmethod
    def create_event(data, token, breadcrumb):
        """
        Create a new event document.

        Args:
            data: Dictionary containing event data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)

        Returns:
            str: The ID of the eventd event document
        """
        try:
            EventService._check_permission(token, "create")

            # Remove _id if present (MongoDB will generate it)
            if "_id" in data:
                del data["_id"]

            # Encode identifier fields (e.g. context.profile_id) to BSON ObjectId
            # so the collection's $jsonSchema validator accepts the document.
            encode_document(data, ID_PROPERTIES, DATE_PROPERTIES)

            # Automatically populate required field: created
            # This is system-managed and should not be provided by the client
            # Use breadcrumb directly as it already has the correct structure
            data["created"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            event_id = mongo.create_document(config.EVENT_COLLECTION_NAME, data)
            logger.info(f"Created event { event_id} for user {token.get('user_id')}")
            return event_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating event: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create event: {error_msg}")

    @staticmethod
    def get_events(token, breadcrumb):
        """
        Get all event documents, sorted by created.at_time ascending.

        Args:
            token: Authentication token
            breadcrumb: Audit breadcrumb

        Returns:
            list: All Event documents
        """
        try:
            EventService._check_permission(token, "read")
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            events = mongo.get_documents(
                config.EVENT_COLLECTION_NAME,
                sort_by=[("created.at_time", ASCENDING)],
            )
            logger.info(
                f"Retrieved {len(events)} events for user {token.get('user_id')}"
            )
            return events
        except Exception as e:
            logger.error(f"Error retrieving events: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve events")

    @staticmethod
    def get_event(event_id, token, breadcrumb):
        """
        Retrieve a specific event document by ID.

        Args:
            event_id: The event ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The event document

        Raises:
            HTTPNotFound: If event is not found
        """
        try:
            EventService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            event = mongo.get_document(config.EVENT_COLLECTION_NAME, event_id)
            if event is None:
                raise HTTPNotFound(f"Event { event_id} not found")

            logger.info(f"Retrieved event { event_id} for user {token.get('user_id')}")
            return event
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving event { event_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve event { event_id}")
