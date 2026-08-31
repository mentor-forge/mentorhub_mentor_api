"""
Plan service for business logic and RBAC.

Inherits shared list and by-id GETs from api_utils.services.PlanService.
Keeps mentor-local write CRUD (create and update) with mentor/admin RBAC.
"""

import logging
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.services import PlanService as SharedPlanService
from api_utils.services.plan_service import (
    PLAN_LIST_FILTERS,
    PLAN_LIST_ORDER,
)

logger = logging.getLogger(__name__)


class PlanService(SharedPlanService):
    """
    Service class for Plan domain operations.

    Inherits GET methods from SharedPlanService:
    - get_plans
    - get_plan

    Implements local write CRUD:
    - create_plan
    - update_plan
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
                    f"Mentor or admin role required to {operation} plan"
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
    def create_plan(cls, data, token, breadcrumb):
        """Create a new plan document."""
        try:
            cls._check_permission(token, "create")
            if "_id" in data:
                del data["_id"]
            data["created"] = breadcrumb
            data["saved"] = breadcrumb
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            plan_id = mongo.create_document(config.PLAN_COLLECTION_NAME, data)
            logger.info(f"Created plan {plan_id} for user {token.get('user_id')}")
            return plan_id
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            raise HTTPInternalServerError(f"Failed to create plan: {e}")

    @classmethod
    def update_plan(cls, plan_id, data, token, breadcrumb):
        """Update an existing plan document."""
        try:
            cls._check_permission(token, "update")
            cls._validate_update_data(data)
            restricted_fields = ["_id", "created", "saved"]
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}
            set_data["saved"] = breadcrumb
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.PLAN_COLLECTION_NAME, document_id=plan_id, set_data=set_data
            )
            if updated is None:
                raise HTTPNotFound(f"Plan {plan_id} not found")
            logger.info(f"Updated plan {plan_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating plan {plan_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update plan {plan_id}")
