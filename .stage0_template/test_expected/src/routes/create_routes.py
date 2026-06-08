"""
Create routes for Flask API.

Provides endpoints for Create domain:
- POST /api/create - Create a new create document
- GET /api/create - Get all create documents
- GET /api/create/<id> - Get a specific create document by ID
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.create_service import CreateService

import logging
logger = logging.getLogger(__name__)


def create_create_routes():
    """
    Create a Flask Blueprint exposing create endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with create routes
    """
    create_routes = Blueprint('create_routes', __name__)
    
    @create_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_create():
        """
        POST /api/create - Create a new create document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created create document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        create_id = CreateService.create_create(data, token, breadcrumb)
        create = CreateService.get_create(create_id, token, breadcrumb)
        
        logger.info(f"create_create Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(create), 201
    
    @create_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_creates():
        """
        GET /api/create - Retrieve infinite scroll batch of sorted, filtered create documents.
        
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
        result = CreateService.get_creates(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_creates Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @create_routes.route('/<create_id>', methods=['GET'])
    @handle_route_exceptions
    def get_create(create_id):
        """
        GET /api/create/<id> - Retrieve a specific create document by ID.
        
        Args:
            create_id: The create ID to retrieve
            
        Returns:
            JSON response with the create document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        create = CreateService.get_create(create_id, token, breadcrumb)
        logger.info(f"get_create Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(create), 200
    
    logger.info("Create Flask Routes Registered")
    return create_routes