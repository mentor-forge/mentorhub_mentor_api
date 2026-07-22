"""
Path routes for Flask API.

Provides endpoints for Path domain:
- POST /api/path - Create a new path document
- GET /api/path - Get all path documents (with optional ?name= query parameter)
- GET /api/path/<id> - Get a specific path document by ID
- PATCH /api/path/<id> - Update a path document
"""

from flask import Blueprint, jsonify, make_response, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.list_request import parse_list_request
from src.services.path_service import (
    PathService,
    PATH_LIST_FILTERS,
    PATH_LIST_ORDER,
)

import logging

logger = logging.getLogger(__name__)


def _paginated_response(items, offset, size):
    """Return a plain-array JSON response with pagination metadata headers."""
    response = make_response(jsonify(items), 200)
    response.headers["X-Pagination-Offset"] = str(offset)
    response.headers["X-Pagination-Size"] = str(size)
    response.headers["X-Pagination-Returned"] = str(len(items))
    return response


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
        GET /api/path - Return a paginated array of Path documents.

        Pagination uses the ``offset``/``size`` request headers. Ordering uses
        ``sort_by``/``order`` query params (validated against the shared Path
        order spec); ``name`` is a contains filter query param. The response
        body is a plain JSON array; pagination metadata is returned via
        ``X-Pagination-*`` response headers.

        Served by the shared ``api_utils.services.PathService``.

        Raises:
            400 Bad Request: If invalid pagination/order parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        offset, size, filters, sort_by = parse_list_request(
            request, PATH_LIST_FILTERS, PATH_LIST_ORDER
        )

        result = PathService.get_paths(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
        )

        logger.info(
            f"get_paths Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return _paginated_response(result, offset, size)

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
