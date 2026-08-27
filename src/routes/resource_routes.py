"""
Resource routes for Flask API.

Provides endpoints for Resource domain:
- POST /api/resource - Create a new resource document
- GET /api/resource - Get all resource documents
- GET /api/resource/<id> - Get a specific resource document by ID
- PATCH /api/resource/<id> - Update a resource document
"""

import logging
from flask import jsonify, request
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from api_utils.routes.shared_get_routes import create_resource_get_routes
from src.services.resource_service import ResourceService

logger = logging.getLogger(__name__)


def create_resource_routes():
    """
    Create a Flask Blueprint exposing resource endpoints.

    GET operations are mounted via create_resource_get_routes(ResourceService).
    Control POST and PATCH are added locally.
    """
    bp = create_resource_get_routes(ResourceService, name="resource_routes")

    @bp.route("", methods=["POST"])
    @handle_route_exceptions
    def create_resource():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        resource_id = ResourceService.create_resource(data, token, breadcrumb)
        resource = ResourceService.get_resource(resource_id, token, breadcrumb)

        logger.info(
            f"create_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(resource), 201

    @bp.route("/<resource_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_resource(resource_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        updated_resource = ResourceService.update_resource(
            resource_id, data, token, breadcrumb
        )

        logger.info(
            f"update_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(updated_resource), 200

    return bp
