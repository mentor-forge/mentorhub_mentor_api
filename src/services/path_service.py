"""
Path service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Path domain.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils.list_query import DEFAULT_OFFSET, DEFAULT_SIZE
from api_utils.services import PathService as SharedPathService
import logging

logger = logging.getLogger(__name__)


class PathService:
    """
    Service class for Path domain operations.

    - List reads delegate to the shared ``api_utils.services.PathService``.
    - Create/update CRUD and the plain by-id read remain local (mentor/admin
      RBAC on update), routed through ``MongoIO``.
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create', 'update')

        Raises:
            HTTPForbidden: If the user lacks the required role.

        RBAC:
            - 'update': requires the mentor or admin role.
            - 'read'/'create': authenticated access only (no additional role check).
        """
        if operation == "update":
            config = Config.get_instance()
            roles = token.get("roles", []) or []
            if config.ROLE_ADMIN in roles:
                return
            if config.ROLE_MENTOR not in roles:
                raise HTTPForbidden(
                    "Mentor or admin role required to update path documents"
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
    def create_path(data, token, breadcrumb):
        """
        Create a new path document.

        Args:
            data: Dictionary containing path data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)

        Returns:
            str: The ID of the created path document
        """
        try:
            PathService._check_permission(token, "create")

            # Remove _id if present (MongoDB will generate it)
            if "_id" in data:
                del data["_id"]

            # Automatically populate required fields: created and saved
            # These are system-managed and should not be provided by the client
            # Use breadcrumb directly as it already has the correct structure
            data["created"] = breadcrumb
            data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            path_id = mongo.create_document(config.PATH_COLLECTION_NAME, data)
            logger.info(f"Created path { path_id} for user {token.get('user_id')}")
            return path_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating path: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create path: {error_msg}")

    @staticmethod
    def get_paths(
        token,
        breadcrumb,
        offset=DEFAULT_OFFSET,
        size=DEFAULT_SIZE,
        filters=None,
        sort_by=None,
    ):
        """
        Return a paginated array of Path documents.

        Delegates to the shared ``api_utils.services.PathService`` list read
        (offset/size pagination, ``name`` contains filter, name-asc default
        order). Returns a plain list; pagination metadata is conveyed via
        response headers by the route layer.
        """
        return SharedPathService.get_paths(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
        )

    @staticmethod
    def get_path(path_id, token, breadcrumb):
        """
        Retrieve a specific path document by ID.

        Args:
            path_id: The path ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The path document

        Raises:
            HTTPNotFound: If path is not found
        """
        try:
            PathService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            path = mongo.get_document(config.PATH_COLLECTION_NAME, path_id)
            if path is None:
                raise HTTPNotFound(f"Path { path_id} not found")

            logger.info(f"Retrieved path { path_id} for user {token.get('user_id')}")
            return path
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving path { path_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve path { path_id}")

    @staticmethod
    def update_path(path_id, data, token, breadcrumb):
        """
        Update a path document.

        Args:
            path_id: The path ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The updated path document

        Raises:
            HTTPNotFound: If path is not found
        """
        try:
            PathService._check_permission(token, "update")
            PathService._validate_update_data(data)

            # Build update data with $set operator (excluding restricted fields)
            restricted_fields = ["_id", "created", "saved"]
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}

            # Automatically update the 'saved' field with current breadcrumb (system-managed)
            # Use breadcrumb directly as it already has the correct structure
            set_data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.PATH_COLLECTION_NAME, document_id=path_id, set_data=set_data
            )

            if updated is None:
                raise HTTPNotFound(f"Path { path_id} not found")

            logger.info(f"Updated path { path_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating path { path_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update path { path_id}")


# Re-export the shared filter/order specs so the route layer can parse list
# request params against the same contract the shared service enforces.
from api_utils.services.path_service import (  # noqa: E402
    PATH_LIST_FILTERS,
    PATH_LIST_ORDER,
)

__all__ = ["PathService", "PATH_LIST_FILTERS", "PATH_LIST_ORDER"]
