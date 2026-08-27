"""
Aggregation routes for Flask API.

Provides endpoints for Resource_Aggregation domain:
- GET /api/aggregation/<resource_id> - Get aggregation detail with related notes
"""

import logging
from api_utils.routes.shared_get_routes import create_aggregation_get_routes
from api_utils.services import AggregationService

logger = logging.getLogger(__name__)


def create_aggregation_routes():
    """
    Create a Flask Blueprint exposing aggregation endpoints.

    Returns:
        Blueprint: Flask Blueprint with aggregation routes
    """
    return create_aggregation_get_routes(AggregationService, name="aggregation_routes")
