"""
Event routes for Flask API.

Provides endpoints for Event domain:
- POST /api/event - Create a new event document
- GET /api/event - Get all event documents
- GET /api/event/<id> - Get a specific event document by ID
"""

import logging
from flask import jsonify, request
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from api_utils.routes.shared_get_routes import create_event_get_routes
from src.services.event_service import EventService

logger = logging.getLogger(__name__)


def create_event_routes():
    """
    Create a Flask Blueprint exposing event endpoints.

    GET list operation is mounted via create_event_get_routes(EventService).
    Control POST and by-id GET are added locally.
    """
    bp = create_event_get_routes(EventService, name="event_routes")

    @bp.route("", methods=["POST"])
    @handle_route_exceptions
    def create_event():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        event = EventService.create_event(data, token, breadcrumb)

        logger.info(
            f"create_event Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(event), 201

    @bp.route("/<event_id>", methods=["GET"])
    @handle_route_exceptions
    def get_event(event_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        event = EventService.get_event(event_id, token, breadcrumb)
        logger.info(
            f"get_event Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(event), 200

    return bp
