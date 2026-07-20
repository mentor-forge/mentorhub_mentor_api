"""
Profile routes for Flask API.

Provides endpoints for Profile domain:
- GET /api/profile - Get the Mentor Dashboard for the current user
- GET /api/profile/<id>/properties - Aggregated mentee activity for Properties hub
- GET /api/profile/<id> - Get composite Profile detail by ID
"""

from flask import Blueprint, jsonify
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.profile_service import ProfileService

import logging

logger = logging.getLogger(__name__)


def create_profile_routes():
    """
    Create a Flask Blueprint exposing profile endpoints.

    Returns:
        Blueprint: Flask Blueprint with profile routes
    """
    profile_routes = Blueprint("profile_routes", __name__)

    @profile_routes.route("", methods=["GET"])
    @handle_route_exceptions
    def get_profiles():
        """
        GET /api/profile - Retrieve the Mentor Dashboard for the current user.

        Resolves the mentor from the JWT identity and returns one card per
        assigned mentee (Profiles whose mentor_id matches the caller). This is a
        read-only, non-paginated endpoint that returns the full set in a
        pre-determined order, so it takes no query parameters.

        Returns:
            JSON array of mentee dashboard cards, each containing basic profile
            info (_id, name, description), learning-journey progress counts
            (library, now, next), and the most recent encounter summary.
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        result = ProfileService.get_profiles(token, breadcrumb)

        logger.info(
            f"get_profiles Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(result), 200

    @profile_routes.route("/<profile_id>/properties", methods=["GET"])
    @handle_route_exceptions
    def get_profile_properties(profile_id):
        """
        GET /api/profile/<id>/properties - Aggregated mentee activity view.
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        result = ProfileService.get_profile_properties(profile_id, token, breadcrumb)
        logger.info(
            f"get_profile_properties Success {str(breadcrumb['at_time'])}, "
            f"{breadcrumb['correlation_id']}"
        )
        return jsonify(result), 200

    @profile_routes.route("/<profile_id>", methods=["GET"])
    @handle_route_exceptions
    def get_profile(profile_id):
        """
        GET /api/profile/<id> - Retrieve composite Profile detail by ID.

        Args:
            profile_id: The profile ID to retrieve

        Returns:
            JSON response with profile, mentee, and encounters
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        profile = ProfileService.get_profile(profile_id, token, breadcrumb)
        logger.info(
            f"get_profile Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(profile), 200

    logger.info("Profile Flask Routes Registered")
    return profile_routes
