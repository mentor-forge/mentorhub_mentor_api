"""
Consume routes for Flask API.

Provides endpoints for Consume domain:
- GET /api/consume - Get all consume documents
- GET /api/consume/<id> - Get a specific consume document by ID
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.consume_service import ConsumeService

import logging
logger = logging.getLogger(__name__)


def create_consume_routes():
    """
    Create a Flask Blueprint exposing consume endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with consume routes
    """
    consume_routes = Blueprint('consume_routes', __name__)
    
    @consume_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_consumes():
        """
        GET /api/consume - Retrieve infinite scroll batch of sorted, filtered consume documents.
        
        Query Parameters:
            name: Optional name filter
            after_id: Cursor for infinite scroll (ID of last item from previous batch, omit for first request)
            limit: Items per batch (default: 10, max: 100)
            sort_by: Field to sort by (default: 'name')
            order: Sort order 'asc' or 'desc' (default: 'asc')
        
        Returns:
            JSON response with infinite scroll results: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None
            }
        
        Raises:
            400 Bad Request: If invalid parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        # Get query parameters
        name = request.args.get('name')
        after_id = request.args.get('after_id')
        limit = request.args.get('limit', 10, type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        
        # Service layer validates parameters and raises HTTPBadRequest if invalid
        # @handle_route_exceptions decorator will catch and format the exception
        result = ConsumeService.get_consumes(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_consumes Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @consume_routes.route('/<consume_id>', methods=['GET'])
    @handle_route_exceptions
    def get_consume(consume_id):
        """
        GET /api/consume/<id> - Retrieve a specific consume document by ID.
        
        Args:
            consume_id: The consume ID to retrieve
            
        Returns:
            JSON response with the consume document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        consume = ConsumeService.get_consume(consume_id, token, breadcrumb)
        logger.info(f"get_consume Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(consume), 200
    
    logger.info("Consume Flask Routes Registered")
    return consume_routes