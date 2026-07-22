"""
Resource routes for Flask API.

Provides endpoints for Resource domain:
- POST /api/resource - Create a new resource document
- GET /api/resource - Get all resource documents (with optional ?name= query parameter)
- GET /api/resource/<id> - Get a specific resource document by ID
- PATCH /api/resource/<id> - Update a resource document
"""

from flask import Blueprint, jsonify, make_response, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.list_request import parse_list_request
from src.services.resource_service import (
    ResourceService,
    RESOURCE_LIST_FILTERS,
    RESOURCE_LIST_ORDER,
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


def create_resource_routes():
    """
    Create a Flask Blueprint exposing resource endpoints.

    Returns:
        Blueprint: Flask Blueprint with resource routes
    """
    resource_routes = Blueprint("resource_routes", __name__)

    @resource_routes.route("", methods=["POST"])
    @handle_route_exceptions
    def create_resource():
        """
        POST /api/resource - Create a new resource document.

        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }

        Returns:
            JSON response with the created resource document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        resource_id = ResourceService.create_resource(data, token, breadcrumb)
        resource = ResourceService.get_resource(resource_id, token, breadcrumb)

        logger.info(
            f"create_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(resource), 201

    @resource_routes.route("", methods=["GET"])
    @handle_route_exceptions
    def get_resources():
        """
        GET /api/resource - Return a paginated array of Resource documents.

        Pagination uses the ``offset``/``size`` request headers. Ordering uses
        ``sort_by``/``order`` query params (validated against the shared
        Resource order spec); filters (e.g. ``name``) are query params per the
        shared Resource filter spec. The response body is a plain JSON array;
        pagination metadata is returned via ``X-Pagination-*`` response headers.

        Served by the shared ``api_utils.services.ResourceService``.

        Raises:
            400 Bad Request: If invalid pagination/order parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        offset, size, filters, sort_by = parse_list_request(
            request, RESOURCE_LIST_FILTERS, RESOURCE_LIST_ORDER
        )

        result = ResourceService.get_resources(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
        )

        logger.info(
            f"get_resources Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return _paginated_response(result, offset, size)

    @resource_routes.route("/<resource_id>", methods=["GET"])
    @handle_route_exceptions
    def get_resource(resource_id):
        """
        GET /api/resource/<id> - Retrieve a specific resource document by ID.

        Args:
            resource_id: The resource ID to retrieve

        Returns:
            JSON response with the resource document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        resource = ResourceService.get_resource(resource_id, token, breadcrumb)
        logger.info(
            f"get_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(resource), 200

    @resource_routes.route("/<resource_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_resource(resource_id):
        """
        PATCH /api/resource/<id> - Update a resource document.

        Args:
            resource_id: The resource ID to update

        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }

        Returns:
            JSON response with the updated resource document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        resource = ResourceService.update_resource(resource_id, data, token, breadcrumb)

        logger.info(
            f"update_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(resource), 200

    logger.info("Resource Flask Routes Registered")
    return resource_routes
