"""
Mentee routes for Flask API.

Provides endpoints for the Mentee domain:
- GET /api/mentee/<profile_id> - Get the mentee notes document for a Profile
  (creating a default document if none exists yet)
- PATCH /api/mentee/<mentee_id> - Update a mentee notes document
"""

from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.mentee_service import MenteeService

import logging

logger = logging.getLogger(__name__)


def create_mentee_routes():
    """
    Create a Flask Blueprint exposing mentee endpoints.

    Returns:
        Blueprint: Flask Blueprint with mentee routes
    """
    mentee_routes = Blueprint("mentee_routes", __name__)

    @mentee_routes.route("/<profile_id>", methods=["GET"])
    @handle_route_exceptions
    def get_mentee(profile_id):
        """
        GET /api/mentee/<profile_id> - Retrieve the mentee notes document.

        Looks up the Mentee document for the given Profile id, creating a
        default document if none exists yet so the caller always receives a
        valid document.

        Args:
            profile_id: The mentee Profile id to retrieve notes for

        Returns:
            JSON response with the mentee notes document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        mentee = MenteeService.get_mentee(profile_id, token, breadcrumb)
        logger.info(
            f"get_mentee Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(mentee), 200

    @mentee_routes.route("/<mentee_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_mentee(mentee_id):
        """
        PATCH /api/mentee/<mentee_id> - Update a mentee notes document.

        Args:
            mentee_id: The Mentee document id to update

        Request body (JSON):
        {
            "description": "new_value",
            "focus": "new_value",
            "status": "archived",
            ...
        }

        Returns:
            JSON response with the updated mentee notes document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        mentee = MenteeService.update_mentee(mentee_id, data, token, breadcrumb)

        logger.info(
            f"update_mentee Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(mentee), 200

    logger.info("Mentee Flask Routes Registered")
    return mentee_routes
