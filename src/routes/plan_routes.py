"""
Plan routes for Flask API.

Provides endpoints for Plan domain:
- POST /api/plan - Create a new plan document
- GET /api/plan - Get all plan documents
- GET /api/plan/<id> - Get a specific plan document by ID
- PATCH /api/plan/<id> - Update a plan document
"""

import logging
from flask import jsonify, request
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from api_utils.routes.shared_get_routes import create_plan_get_routes
from src.services.plan_service import PlanService

logger = logging.getLogger(__name__)


def create_plan_routes():
    """
    Create a Flask Blueprint exposing plan endpoints.

    GET operations are mounted via create_plan_get_routes(PlanService).
    Control POST and PATCH are added locally.
    """
    bp = create_plan_get_routes(PlanService, name="plan_routes")

    @bp.route("", methods=["POST"])
    @handle_route_exceptions
    def create_plan():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        plan_id = PlanService.create_plan(data, token, breadcrumb)
        plan = PlanService.get_plan(plan_id, token, breadcrumb)

        logger.info(
            f"create_plan Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(plan), 201

    @bp.route("/<plan_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_plan(plan_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        updated_plan = PlanService.update_plan(plan_id, data, token, breadcrumb)

        logger.info(
            f"update_plan Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(updated_plan), 200

    return bp
