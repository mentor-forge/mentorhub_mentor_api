"""
Path routes for Flask API.

Provides endpoints for Path domain:
- POST /api/path - Create a new path document
- GET /api/path - Get all path documents (with optional ?name= query parameter)
- GET /api/path/<id> - Get a specific path document by ID
- PATCH /api/path/<id> - Update a path document
"""

from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.path_service import PathService

import logging

logger = logging.getLogger(__name__)


def create_path_routes():
    """
    Create a Flask Blueprint exposing path endpoints.

    Returns:
        Blueprint: Flask Blueprint with path routes
    """
    path_routes = Blueprint("path_routes", __name__)

    @path_routes.route("", methods=["POST"])
    @handle_route_exceptions
    def create_path():
        """
        POST /api/path - Create a new path document.

        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }

        Returns:
            JSON response with the created path document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        path_id = PathService.create_path(data, token, breadcrumb)
        path = PathService.get_path(path_id, token, breadcrumb)

        logger.info(
            f"create_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(path), 201

    @path_routes.route("", methods=["GET"])
    @handle_route_exceptions
    def get_paths():
        """
        GET /api/path - Retrieve all path documents (sorted by name ascending).

        Query Parameters:
            name: Optional name filter (partial, case-insensitive)

        Returns:
            JSON array of all matching path documents
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        name = request.args.get("name")

        result = PathService.get_paths(token, breadcrumb, name=name)

        logger.info(
            f"get_paths Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(result), 200

    @path_routes.route("/<path_id>", methods=["GET"])
    @handle_route_exceptions
    def get_path(path_id):
        """
        GET /api/path/<id> - Retrieve a specific path document by ID.

        Args:
            path_id: The path ID to retrieve

        Returns:
            JSON response with the path document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        path = PathService.get_path(path_id, token, breadcrumb)
        logger.info(
            f"get_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(path), 200

    @path_routes.route("/<path_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_path(path_id):
        """
        PATCH /api/path/<id> - Update a path document.

        Args:
            path_id: The path ID to update

        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }

        Returns:
            JSON response with the updated path document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        path = PathService.update_path(path_id, data, token, breadcrumb)

        logger.info(
            f"update_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(path), 200

    logger.info("Path Flask Routes Registered")
    return path_routes
