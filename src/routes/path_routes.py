"""
Path routes for Flask API.

Provides endpoints for Path domain:
- POST /api/path - Create a new path document
- GET /api/path - Get all path documents
- GET /api/path/<id> - Get a specific path document by ID
- PATCH /api/path/<id> - Update a path document
"""

import logging
from flask import jsonify, request
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from api_utils.routes.shared_get_routes import create_path_get_routes
from src.services.path_service import PathService

logger = logging.getLogger(__name__)


def create_path_routes():
    """
    Create a Flask Blueprint exposing path endpoints.

    GET operations are mounted via create_path_get_routes(PathService).
    Control POST and PATCH are added locally.
    """
    bp = create_path_get_routes(PathService, name="path_routes")

    @bp.route("", methods=["POST"])
    @handle_route_exceptions
    def create_path():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        path_id = PathService.create_path(data, token, breadcrumb)
        path = PathService.get_path(path_id, token, breadcrumb)

        logger.info(
            f"create_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(path), 201

    @bp.route("/<path_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_path(path_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        updated_path = PathService.update_path(path_id, data, token, breadcrumb)

        logger.info(
            f"update_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(updated_path), 200

    return bp
