"""
Plan service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Plan domain.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.mongo_utils.list_query import (
    DEFAULT_OFFSET,
    DEFAULT_SIZE,
    build_match_filter,
    build_sort_by,
    execute_list_query,
)
import logging

logger = logging.getLogger(__name__)

# Plan remains a mentor-only local domain, but adopts the shared header
# pagination + sort_by/order + filter conventions for list consistency.
PLAN_LIST_FILTERS = {
    "name": {"type": "contains", "field": "name"},
}

PLAN_LIST_ORDER = {
    "default": {"field": "name", "order": "asc"},
    "allowed": {"name": ("asc", "desc")},
}


class PlanService:
    """
    Service class for Plan domain operations.

    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Plan domain
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create', 'update')

        Raises:
            HTTPForbidden: If user doesn't have required permission

        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).

        Example RBAC implementation:
            if operation == 'update':
                # Update requires admin role
                if 'admin' not in token.get('roles', []):
                    raise HTTPForbidden("Admin role required to update plan documents")
            elif operation == 'create':
                # Create requires staff or admin role
                if not any(role in token.get('roles', []) for role in ['staff', 'admin']):
                    raise HTTPForbidden("Staff or admin role required to create plan documents")
            elif operation == 'read':
                # Read requires any authenticated user (no additional check needed)
                pass
        """
        pass

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
    def create_plan(data, token, breadcrumb):
        """
        Create a new plan document.

        Args:
            data: Dictionary containing plan data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)

        Returns:
            str: The ID of the created plan document
        """
        try:
            PlanService._check_permission(token, "create")

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
            plan_id = mongo.create_document(config.PLAN_COLLECTION_NAME, data)
            logger.info(f"Created plan { plan_id} for user {token.get('user_id')}")
            return plan_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating plan: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create plan: {error_msg}")

    @staticmethod
    def get_plans(
        token,
        breadcrumb,
        offset=DEFAULT_OFFSET,
        size=DEFAULT_SIZE,
        filters=None,
        sort_by=None,
    ):
        """
        Return a paginated array of plan documents.

        Plan is mentor-only and stays local, but the list adopts the shared
        conventions: ``offset``/``size`` pagination, ``sort_by``/``order``
        (default name asc), and an optional ``name`` contains filter. Returns a
        plain list; pagination metadata is conveyed via response headers by the
        route layer.
        """
        try:
            PlanService._check_permission(token, "read")
            config = Config.get_instance()

            match = build_match_filter({}, filters or {}, PLAN_LIST_FILTERS)
            if sort_by is None:
                default = PLAN_LIST_ORDER["default"]
                sort_by = build_sort_by(
                    default["field"], default["order"], PLAN_LIST_ORDER
                )

            plans = execute_list_query(
                config.PLAN_COLLECTION_NAME,
                match=match,
                sort_by=sort_by,
                offset=offset,
                size=size,
            )
            logger.info(f"Retrieved {len(plans)} plans for user {token.get('user_id')}")
            return plans
        except (HTTPBadRequest, HTTPForbidden):
            raise
        except Exception as e:
            logger.error(f"Error retrieving plans: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve plans")

    @staticmethod
    def get_plan(plan_id, token, breadcrumb):
        """
        Retrieve a specific plan document by ID.

        Args:
            plan_id: The plan ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The plan document

        Raises:
            HTTPNotFound: If plan is not found
        """
        try:
            PlanService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            plan = mongo.get_document(config.PLAN_COLLECTION_NAME, plan_id)
            if plan is None:
                raise HTTPNotFound(f"Plan { plan_id} not found")

            logger.info(f"Retrieved plan { plan_id} for user {token.get('user_id')}")
            return plan
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving plan { plan_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve plan { plan_id}")

    @staticmethod
    def update_plan(plan_id, data, token, breadcrumb):
        """
        Update a plan document.

        Args:
            plan_id: The plan ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The updated plan document

        Raises:
            HTTPNotFound: If plan is not found
        """
        try:
            PlanService._check_permission(token, "update")
            PlanService._validate_update_data(data)

            # Build update data with $set operator (excluding restricted fields)
            restricted_fields = ["_id", "created", "saved"]
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}

            # Automatically update the 'saved' field with current breadcrumb (system-managed)
            # Use breadcrumb directly as it already has the correct structure
            set_data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.PLAN_COLLECTION_NAME, document_id=plan_id, set_data=set_data
            )

            if updated is None:
                raise HTTPNotFound(f"Plan { plan_id} not found")

            logger.info(f"Updated plan { plan_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating plan { plan_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update plan { plan_id}")
