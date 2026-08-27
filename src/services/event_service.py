"""
Event service for business logic and RBAC.

Inherits shared list and read methods from api_utils.services.EventService.
Keeps mentor-local event creation with mentor/admin RBAC.
"""

import logging
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils import encode_document
from api_utils.services import EventService as SharedEventService
from api_utils.services.event_service import (
    EVENT_LIST_FILTERS,
    EVENT_LIST_ORDER,
)

logger = logging.getLogger(__name__)

ID_PROPERTIES = ["_id", "profile_id"]
DATE_PROPERTIES = []


class EventService(SharedEventService):
    """
    Service class for Event domain operations.

    Inherits GET list operations from SharedEventService.
    Implements local create and by-id get.
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """
        Inbound RBAC check: create requires mentor or admin.
        Read operations delegate to parent.
        """
        config = Config.get_instance()
        roles = token.get("roles", []) or []
        if config.ROLE_ADMIN in roles:
            return
        if operation == "create":
            if config.ROLE_MENTOR not in roles:
                raise HTTPForbidden("Mentor or admin role required to create event")
        else:
            if hasattr(super(), "_check_permission"):
                super()._check_permission(token, operation)

    @classmethod
    def create_event(cls, data, token, breadcrumb):
        """Create a new event document (mentor-local)."""
        try:
            cls._check_permission(token, "create")

            if "_id" in data:
                del data["_id"]

            encode_document(data, ID_PROPERTIES, DATE_PROPERTIES)

            data["created"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            event_id = mongo.create_document(config.EVENT_COLLECTION_NAME, data)
            logger.info(f"Created event {event_id} for user {token.get('user_id')}")
            return event_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating event: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create event: {error_msg}")

    @classmethod
    def get_event(cls, event_id, token, breadcrumb):
        """Retrieve a specific event document by ID."""
        try:
            if hasattr(super(), "get_event"):
                return super().get_event(event_id, token, breadcrumb)
            cls._check_permission(token, "read")
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            event = mongo.get_document(config.EVENT_COLLECTION_NAME, event_id)
            if event is None:
                raise HTTPNotFound(f"Event {event_id} not found")
            logger.info(f"Retrieved event {event_id} for user {token.get('user_id')}")
            return event
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving event {event_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve event {event_id}")


__all__ = ["EventService", "EVENT_LIST_FILTERS", "EVENT_LIST_ORDER"]
