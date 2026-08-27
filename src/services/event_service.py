"""
Event service for business logic and RBAC.

Inherits shared list and create methods from api_utils.services.EventService.
Implements local get_event by ID.
"""

import logging
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.services import EventService as SharedEventService
from api_utils.services.event_service import (
    EVENT_LIST_FILTERS,
    EVENT_LIST_ORDER,
)

logger = logging.getLogger(__name__)


class EventService(SharedEventService):
    """
    Service class for Event domain operations.

    Inherits create_event and get_events from SharedEventService.
    Implements local get_event for by-id retrieval.
    """

    @classmethod
    def get_event(cls, event_id, token, breadcrumb):
        """Retrieve a specific event document by ID."""
        try:
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
