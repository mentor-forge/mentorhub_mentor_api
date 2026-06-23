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
from api_utils.mongo_utils import execute_infinite_scroll_query
import logging

logger = logging.getLogger(__name__)

# Allowed sort fields for Plan domain
ALLOWED_SORT_FIELDS = [
    "name",
    "description",
    "status",
    "created.at_time",
    "saved.at_time",
]

# The Plan list field is exposed in the API as `steps` but stored in MongoDB as
# `checklist` (the data dictionary uses `checklist` with additionalProperties:false,
# so a literal `steps` key would fail schema validation on write).
API_LIST_FIELD = "steps"
STORAGE_LIST_FIELD = "checklist"
MAX_STEPS = 100
MAX_STEP_LENGTH = 255


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
    def _validate_steps(steps):
        """
        Validate the API `steps` value.

        Args:
            steps: The value supplied under the API `steps` key.

        Raises:
            HTTPBadRequest: If steps is not a list of non-empty single-line
                strings within length/count limits.
        """
        if not isinstance(steps, list):
            raise HTTPBadRequest("steps must be a list")
        if len(steps) > MAX_STEPS:
            raise HTTPBadRequest(f"steps cannot contain more than {MAX_STEPS} items")
        for index, item in enumerate(steps):
            if not isinstance(item, str):
                raise HTTPBadRequest(f"steps[{index}] must be a string")
            if not item.strip():
                raise HTTPBadRequest(f"steps[{index}] must not be empty")
            if len(item) > MAX_STEP_LENGTH:
                raise HTTPBadRequest(
                    f"steps[{index}] must be at most {MAX_STEP_LENGTH} characters"
                )
            if "\t" in item or "\n" in item:
                raise HTTPBadRequest(
                    f"steps[{index}] must not contain tab or newline characters"
                )

    @staticmethod
    def _map_steps_to_storage(data):
        """
        Translate an inbound API payload (`steps`) into storage form (`checklist`).

        Returns a shallow copy so the caller's dict is not mutated. Validates
        `steps` when present and never leaves a top-level `steps` key (which
        would fail MongoDB schema validation).

        Args:
            data: Inbound request data (may contain `steps`).

        Returns:
            dict: A copy with `steps` renamed to `checklist` when present.
        """
        result = dict(data)
        if API_LIST_FIELD in result:
            steps = result.pop(API_LIST_FIELD)
            PlanService._validate_steps(steps)
            result[STORAGE_LIST_FIELD] = steps
        return result

    @staticmethod
    def _map_checklist_to_api(document):
        """
        Translate a stored document (`checklist`) into API form (`steps`).

        Args:
            document: A plan document from MongoDB (or None).

        Returns:
            The document with `checklist` renamed to `steps`, or the input
            unchanged when it is falsy or has no `checklist`.
        """
        if not document or STORAGE_LIST_FIELD not in document:
            return document
        result = dict(document)
        result[API_LIST_FIELD] = result.pop(STORAGE_LIST_FIELD)
        return result

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

            # Translate API `steps` -> storage `checklist` (validates steps)
            data = PlanService._map_steps_to_storage(data)

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
        except (HTTPForbidden, HTTPBadRequest):
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating plan: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create plan: {error_msg}")

    @staticmethod
    def get_plans(
        token,
        breadcrumb,
        name=None,
        after_id=None,
        limit=10,
        sort_by="name",
        order="asc",
    ):
        """
        Get infinite scroll batch of sorted, filtered plan documents.

        Args:
            token: Authentication token
            breadcrumb: Audit breadcrumb
            name: Optional name filter (simple search)
            after_id: Cursor (ID of last item from previous batch, None for first request)
            limit: Items per batch
            sort_by: Field to sort by
            order: Sort order ('asc' or 'desc')

        Returns:
            dict: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None  # ID of last item, or None if no more
            }

        Raises:
            HTTPBadRequest: If invalid parameters provided
        """
        try:
            PlanService._check_permission(token, "read")
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.PLAN_COLLECTION_NAME)
            result = execute_infinite_scroll_query(
                collection,
                name=name,
                after_id=after_id,
                limit=limit,
                sort_by=sort_by,
                order=order,
                allowed_sort_fields=ALLOWED_SORT_FIELDS,
            )
            # Expose the stored `checklist` as `steps` in each item
            result["items"] = [
                PlanService._map_checklist_to_api(item) for item in result["items"]
            ]
            logger.info(
                f"Retrieved {len(result['items'])} plans (has_more={result['has_more']}) "
                f"for user {token.get('user_id')}"
            )
            return result
        except HTTPBadRequest:
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
            return PlanService._map_checklist_to_api(plan)
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

            # Translate API `steps` -> storage `checklist` (validates steps)
            data = PlanService._map_steps_to_storage(data)

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
            return PlanService._map_checklist_to_api(updated)
        except (HTTPForbidden, HTTPNotFound, HTTPBadRequest):
            raise
        except Exception as e:
            logger.error(f"Error updating plan { plan_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update plan { plan_id}")
