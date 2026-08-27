"""
Aggregation routes for Flask API.

Provides endpoints for Resource_Aggregation domain:
- GET /api/aggregation/<resource_id> - Get aggregation detail with related notes
"""

import logging
from flask import Blueprint, jsonify
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.services import AggregationService

logger = logging.getLogger(__name__)


def create_aggregation_routes():
    """
    Create a Flask Blueprint exposing aggregation endpoints.

    Returns:
        Blueprint: Flask Blueprint with aggregation routes
    """
    aggregation_routes = Blueprint("aggregation_routes", __name__)

    @aggregation_routes.route("/<resource_id>", methods=["GET"])
    @handle_route_exceptions
    def get_aggregation_detail(resource_id):
        """
        GET /api/aggregation/<resource_id> - Retrieve aggregation detail composite.

        Returns:
            JSON response with aggregation metrics and related notes
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        detail = AggregationService.get_aggregation_detail(
            resource_id, token, breadcrumb
        )

        logger.info(
            f"get_aggregation_detail Success {str(breadcrumb['at_time'])}, "
            f"{breadcrumb['correlation_id']}"
        )
        return jsonify(detail), 200

    logger.info("Aggregation Flask Routes Registered")
    return aggregation_routes
