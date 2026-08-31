"""
Profile routes for Flask API.

Provides endpoints for Profile domain:
- GET /api/profile - Get the Mentor Dashboard for the current user
- GET /api/profile/<id>/properties - Aggregated mentee activity for Properties hub
- GET /api/profile/<id> - Get composite Profile detail by ID
"""

import logging
from flask import jsonify
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from api_utils.routes.shared_get_routes import create_profile_get_routes
from src.services.profile_service import ProfileService

logger = logging.getLogger(__name__)


def create_profile_routes():
    """
    Create a Flask Blueprint exposing profile endpoints.

    GET operations (dashboard and profile detail) are mounted via
    create_profile_get_routes(ProfileService).
    Properties hub is added locally.
    """
    bp = create_profile_get_routes(ProfileService, name="profile_routes")

    @bp.route("/<profile_id>/properties", methods=["GET"])
    @handle_route_exceptions
    def get_profile_properties(profile_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        result = ProfileService.get_profile_properties(profile_id, token, breadcrumb)
        logger.info(
            f"get_profile_properties Success {str(breadcrumb['at_time'])}, "
            f"{breadcrumb['correlation_id']}"
        )
        return jsonify(result), 200

    return bp
