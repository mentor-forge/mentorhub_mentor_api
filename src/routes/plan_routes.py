"""
Plan routes for Flask API.

Provides endpoints for Plan domain:
- POST /api/plan - Create a new plan document
- GET /api/plan - Get all plan documents (with optional ?name= query parameter)
- GET /api/plan/<id> - Get a specific plan document by ID
- PATCH /api/plan/<id> - Update a plan document
"""

from flask import Blueprint, jsonify, make_response, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.list_request import parse_list_request
from src.services.plan_service import PlanService, PLAN_LIST_FILTERS, PLAN_LIST_ORDER

import logging

logger = logging.getLogger(__name__)


def _paginated_response(items, offset, size):
    """Return a plain-array JSON response with pagination metadata headers."""
    response = make_response(jsonify(items), 200)
    response.headers["X-Pagination-Offset"] = str(offset)
    response.headers["X-Pagination-Size"] = str(size)
    response.headers["X-Pagination-Returned"] = str(len(items))
    return response


def create_plan_routes():
    """
    Create a Flask Blueprint exposing plan endpoints.

    Returns:
        Blueprint: Flask Blueprint with plan routes
    """
    plan_routes = Blueprint("plan_routes", __name__)

    @plan_routes.route("", methods=["POST"])
    @handle_route_exceptions
    def create_plan():
        """
        POST /api/plan - Create a new plan document.

        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }

        Returns:
            JSON response with the created plan document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        plan_id = PlanService.create_plan(data, token, breadcrumb)
        plan = PlanService.get_plan(plan_id, token, breadcrumb)

        logger.info(
            f"create_plan Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(plan), 201

    @plan_routes.route("", methods=["GET"])
    @handle_route_exceptions
    def get_plans():
        """
        GET /api/plan - Return a paginated array of plan documents.

        Pagination uses the ``offset``/``size`` request headers. Ordering uses
        ``sort_by``/``order`` query params (default name asc); ``name`` is an
        optional contains filter query param. The response body is a plain JSON
        array; pagination metadata is returned via ``X-Pagination-*`` response
        headers.

        Raises:
            400 Bad Request: If invalid pagination/order parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        offset, size, filters, sort_by = parse_list_request(
            request, PLAN_LIST_FILTERS, PLAN_LIST_ORDER
        )

        result = PlanService.get_plans(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
        )

        logger.info(
            f"get_plans Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return _paginated_response(result, offset, size)

    @plan_routes.route("/<plan_id>", methods=["GET"])
    @handle_route_exceptions
    def get_plan(plan_id):
        """
        GET /api/plan/<id> - Retrieve a specific plan document by ID.

        Args:
            plan_id: The plan ID to retrieve

        Returns:
            JSON response with the plan document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        plan = PlanService.get_plan(plan_id, token, breadcrumb)
        logger.info(
            f"get_plan Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(plan), 200

    @plan_routes.route("/<plan_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_plan(plan_id):
        """
        PATCH /api/plan/<id> - Update a plan document.

        Args:
            plan_id: The plan ID to update

        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }

        Returns:
            JSON response with the updated plan document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        plan = PlanService.update_plan(plan_id, data, token, breadcrumb)

        logger.info(
            f"update_plan Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(plan), 200

    logger.info("Plan Flask Routes Registered")
    return plan_routes
