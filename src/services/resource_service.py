"""
Resource service for business logic and RBAC.

The Resource **list** read is served by the shared
``api_utils.services.ResourceService`` (harvested into api_utils 0.5.x). This
module keeps only the mentor-local pieces the shared service does not own:
create/update CRUD and the plain by-id read used by this API's contract.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils.list_query import DEFAULT_OFFSET, DEFAULT_SIZE
from api_utils.services import ResourceService as SharedResourceService
import logging

logger = logging.getLogger(__name__)


class ResourceService:
    """
    Service class for Resource domain operations.

    - List reads delegate to the shared ``api_utils.services.ResourceService``.
    - Create/update CRUD and the plain by-id read remain local, routed through
      ``MongoIO``.
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Placeholder RBAC hook (authenticated access only for now).
        """
        pass

    @staticmethod
    def _validate_update_data(data):
        """Reject updates that target system-managed fields."""
        restricted_fields = ["_id", "created", "saved"]
        for field in restricted_fields:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")

    @staticmethod
    def create_resource(data, token, breadcrumb):
        """Create a new resource document (mentor-local CRUD)."""
        try:
            ResourceService._check_permission(token, "create")

            if "_id" in data:
                del data["_id"]

            data["created"] = breadcrumb
            data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource_id = mongo.create_document(config.RESOURCE_COLLECTION_NAME, data)
            logger.info(
                f"Created resource { resource_id} for user {token.get('user_id')}"
            )
            return resource_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating resource: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create resource: {error_msg}")

    @staticmethod
    def get_resources(
        token,
        breadcrumb,
        offset=DEFAULT_OFFSET,
        size=DEFAULT_SIZE,
        filters=None,
        sort_by=None,
    ):
        """
        Return a paginated array of Resource documents.

        Delegates to the shared ``api_utils.services.ResourceService`` list read
        (offset/size pagination, filter/order per the shared spec). Returns a
        plain list; pagination metadata is conveyed via response headers by the
        route layer.
        """
        return SharedResourceService.get_resources(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
        )

    @staticmethod
    def get_resource(resource_id, token, breadcrumb):
        """Retrieve a specific resource document by ID (mentor-local read)."""
        try:
            ResourceService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_id)
            if resource is None:
                raise HTTPNotFound(f"Resource { resource_id} not found")

            logger.info(
                f"Retrieved resource { resource_id} for user {token.get('user_id')}"
            )
            return resource
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving resource { resource_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve resource { resource_id}")

    @staticmethod
    def update_resource(resource_id, data, token, breadcrumb):
        """Update a resource document (mentor-local CRUD)."""
        try:
            ResourceService._check_permission(token, "update")
            ResourceService._validate_update_data(data)

            restricted_fields = ["_id", "created", "saved"]
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}
            set_data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.RESOURCE_COLLECTION_NAME,
                document_id=resource_id,
                set_data=set_data,
            )

            if updated is None:
                raise HTTPNotFound(f"Resource { resource_id} not found")

            logger.info(
                f"Updated resource { resource_id} for user {token.get('user_id')}"
            )
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating resource { resource_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update resource { resource_id}")


# Re-export the shared filter/order specs so the route layer can parse list
# request params against the same contract the shared service enforces.
from api_utils.services.resource_service import (  # noqa: E402
    RESOURCE_LIST_FILTERS,
    RESOURCE_LIST_ORDER,
)

__all__ = ["ResourceService", "RESOURCE_LIST_FILTERS", "RESOURCE_LIST_ORDER"]
