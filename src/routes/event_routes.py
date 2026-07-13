"""
Event routes for Flask API.

Provides endpoints for Create domain:
- POST /api/event - Create a new event document
- GET /api/event - Get all event documents
- GET /api/event/<id> - Get a specific event document by ID
"""

from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.event_service import EventService

import logging

logger = logging.getLogger(__name__)


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
        GET /api/event - Return all Event documents, sorted by created.at_time ascending.

        Returns:
            JSON array of Event documents
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        result = EventService.get_events(token, breadcrumb)

        logger.info(
            f"get_events Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(result), 200

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
