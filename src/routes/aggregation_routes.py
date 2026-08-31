"""
Aggregation routes for Flask API.

Provides:
- GET /api/aggregation/<resource_id> — aggregation document or null when the
  Resource is missing/hidden or no aggregation row exists (api-utils 1.0.0).
"""

import logging
from api_utils.routes.shared_get_routes import create_aggregation_get_routes
from src.services.aggregation_service import AggregationService

logger = logging.getLogger(__name__)


def create_aggregation_routes():
    """
    Create a Flask Blueprint exposing aggregation endpoints.

    Passes the local AggregationService subclass so factory dispatch stays on
    the Mentor service module (never api_utils.services directly).

    Returns:
        Blueprint: Flask Blueprint with aggregation routes
    """
    return create_aggregation_get_routes(AggregationService, name="aggregation_routes")
