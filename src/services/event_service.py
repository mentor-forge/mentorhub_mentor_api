"""
Event service for business logic and RBAC.

The Event **list** read is served by the shared
``api_utils.services.EventService`` (harvested into api_utils 0.5.x). The
mentor-local ``create_event`` (with ObjectId encoding of ``profile_id``) and the
plain by-id ``get_event`` read remain here until Event CRUD is separately
harvested.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils import encode_document
from api_utils.mongo_utils.list_query import DEFAULT_OFFSET, DEFAULT_SIZE
from api_utils.services import EventService as SharedEventService
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

    - List reads delegate to the shared ``api_utils.services.EventService``.
    - ``create_event`` and the plain by-id ``get_event`` remain local, routed
      through ``MongoIO``.
    """

    @staticmethod
    def _check_permission(token, operation):
        """Placeholder RBAC hook (authenticated access only for now)."""
        pass

    @staticmethod
    def create_event(data, token, breadcrumb):
        """
        Create a new event document (mentor-local).

        Encodes identifier fields (e.g. ``context.profile_id``) to BSON
        ObjectId so the collection's ``$jsonSchema`` validator accepts the
        document, then stamps the system-managed ``created`` breadcrumb.
        """
        try:
            EventService._check_permission(token, "create")

            if "_id" in data:
                del data["_id"]

            encode_document(data, ID_PROPERTIES, DATE_PROPERTIES)

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
    def get_events(
        token,
        breadcrumb,
        offset=DEFAULT_OFFSET,
        size=DEFAULT_SIZE,
        filters=None,
        sort_by=None,
        *,
        profile_id=None,
    ):
        """
        Return a paginated array of Event documents.

        Delegates to the shared ``api_utils.services.EventService`` list read
        (offset/size pagination, ``type`` filter and ``EVENT_LIST_ORDER``
        ordering, optional ``profile_id`` scope on ``context.profile_id``).
        """
        return SharedEventService.get_events(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
            profile_id=profile_id,
        )

    @staticmethod
    def get_event(event_id, token, breadcrumb):
        """Retrieve a specific event document by ID (mentor-local read)."""
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


# Re-export the shared filter/order specs so the route layer can parse list
# request params against the same contract the shared service enforces.
from api_utils.services.event_service import (  # noqa: E402
    EVENT_LIST_FILTERS,
    EVENT_LIST_ORDER,
)

__all__ = ["EventService", "EVENT_LIST_FILTERS", "EVENT_LIST_ORDER"]
