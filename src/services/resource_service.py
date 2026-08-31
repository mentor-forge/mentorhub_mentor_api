"""
Resource service for business logic and RBAC.

Inherits shared list and by-id GETs from api_utils.services.ResourceService.
Keeps mentor-local write CRUD (create and update) with mentor/admin RBAC.
"""

import logging
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.services import ResourceService as SharedResourceService
from api_utils.services.resource_service import (
    RESOURCE_LIST_FILTERS,
    RESOURCE_LIST_ORDER,
)

logger = logging.getLogger(__name__)


class ResourceService(SharedResourceService):
    """
    Service class for Resource domain operations.

    Inherits GET methods from SharedResourceService:
    - get_resources
    - get_resource
    - get_resources_by_ids

    Implements local write CRUD:
    - create_resource
    - update_resource
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """
        Inbound RBAC check: create/update requires mentor or admin.
        Read operations delegate to parent (no-op; outbound filtering handles visibility).
        """
        config = Config.get_instance()
        roles = token.get("roles", []) or []
        if config.ROLE_ADMIN in roles:
            return
        if operation in ("create", "update"):
            if config.ROLE_MENTOR not in roles:
                raise HTTPForbidden(
                    f"Mentor or admin role required to {operation} resource"
                )
        else:
            super()._check_permission(token, operation)

    @classmethod
    def _validate_update_data(cls, data):
        """Reject updates that target system-managed fields."""
        restricted_fields = ["_id", "created", "saved"]
        for field in restricted_fields:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")

    @classmethod
    def create_resource(cls, data, token, breadcrumb):
        """Create a new resource document (mentor-local CRUD)."""
        try:
            cls._check_permission(token, "create")

            if "_id" in data:
                del data["_id"]

            data["created"] = breadcrumb
            data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource_id = mongo.create_document(config.RESOURCE_COLLECTION_NAME, data)
            logger.info(
                f"Created resource {resource_id} for user {token.get('user_id')}"
            )
            return resource_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating resource: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create resource: {error_msg}")

    @classmethod
    def update_resource(cls, resource_id, data, token, breadcrumb):
        """Update a resource document (mentor-local CRUD)."""
        try:
            cls._check_permission(token, "update")
            cls._validate_update_data(data)

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
                raise HTTPNotFound(f"Resource {resource_id} not found")

            logger.info(
                f"Updated resource {resource_id} for user {token.get('user_id')}"
            )
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating resource {resource_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update resource {resource_id}")
