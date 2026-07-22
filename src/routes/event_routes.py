"""
Event routes for Flask API.

Provides endpoints for Create domain:
- POST /api/event - Create a new event document
- GET /api/event - Get all event documents
- GET /api/event/<id> - Get a specific event document by ID
"""

from flask import Blueprint, jsonify, make_response, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.list_request import parse_list_request
from src.services.event_service import (
    EventService,
    EVENT_LIST_FILTERS,
    EVENT_LIST_ORDER,
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


def create_event_routes():
    """
    Create a Flask Blueprint exposing event endpoints.

    Returns:
        Blueprint: Flask Blueprint with event routes
    """
    event_routes = Blueprint("event_routes", __name__)

    @event_routes.route("", methods=["POST"])
    @handle_route_exceptions
    def create_event():
        """
        POST /api/event - Create a new event document.

        Request body (JSON):
        {
            "type": "login",
            "context": { "profile_id": "507f1f77bcf86cd799439011" }
        }

        Returns:
            JSON response with the created event document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        event_id = EventService.create_event(data, token, breadcrumb)
        event = EventService.get_event(event_id, token, breadcrumb)

        logger.info(
            f"create_event Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(event), 201

    @event_routes.route("", methods=["GET"])
    @handle_route_exceptions
    def get_events():
        """
        GET /api/event - Return a paginated array of Event documents.

        Pagination uses the ``offset``/``size`` request headers. Ordering uses
        ``sort_by``/``order`` query params (validated against ``EVENT_LIST_ORDER``);
        ``type`` is a filter query param and ``profile_id`` scopes on
        ``context.profile_id``. The response body is a plain JSON array;
        pagination metadata is returned via ``X-Pagination-*`` response headers.

        Served by the shared ``api_utils.services.EventService``.

        Raises:
            400 Bad Request: If invalid pagination/order parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        offset, size, filters, sort_by = parse_list_request(
            request, EVENT_LIST_FILTERS, EVENT_LIST_ORDER
        )
        profile_id = request.args.get("profile_id")

        result = EventService.get_events(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
            profile_id=profile_id,
        )

        logger.info(
            f"get_events Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return _paginated_response(result, offset, size)

    @event_routes.route("/<event_id>", methods=["GET"])
    @handle_route_exceptions
    def get_event(event_id):
        """
        GET /api/event/<id> - Retrieve a specific event document by ID.

        Args:
            event_id: The event ID to retrieve

        Returns:
            JSON response with the event document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        event = EventService.get_event(event_id, token, breadcrumb)
        logger.info(
            f"get_event Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(event), 200

    logger.info("Create Flask Routes Registered")
    return event_routes
