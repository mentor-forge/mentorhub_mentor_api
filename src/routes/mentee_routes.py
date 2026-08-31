"""
Mentee routes for Flask API.

Provides endpoints for the Mentee domain:
- GET /api/mentee/<profile_id> - Get the mentee notes document for a Profile
- PATCH /api/mentee/<mentee_id> - Update a mentee notes document
"""

import logging
from flask import jsonify, request
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from api_utils.routes.shared_get_routes import create_mentee_get_routes
from src.services.mentee_service import MenteeService

logger = logging.getLogger(__name__)


def create_mentee_routes():
    """
    Create a Flask Blueprint exposing mentee endpoints.

    GET operation is mounted via create_mentee_get_routes(MenteeService).
    Control PATCH is added locally.
    """
    bp = create_mentee_get_routes(MenteeService, name="mentee_routes")

    @bp.route("/<mentee_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_mentee(mentee_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        mentee = MenteeService.update_mentee(mentee_id, data, token, breadcrumb)

        logger.info(
            f"update_mentee Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(mentee), 200

    return bp
