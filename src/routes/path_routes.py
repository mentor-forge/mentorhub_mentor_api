"""
Path routes for Flask API.

Provides endpoints for Path domain:
- POST /api/path - Create a new path document
- GET /api/path - Get all path documents (with optional ?name= query parameter)
- GET /api/path/<id> - Get a specific path document by ID
- PATCH /api/path/<id> - Update a path document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.path_service import PathService

import logging
logger = logging.getLogger(__name__)


def create_path_routes():
    """
    Create a Flask Blueprint exposing path endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with path routes
    """
    path_routes = Blueprint('path_routes', __name__)
    
    @path_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_path():
        """
        POST /api/path - Create a new path document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created path document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        path_id = PathService.create_path(data, token, breadcrumb)
        path = PathService.get_path(path_id, token, breadcrumb)
        
        logger.info(f"create_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(path), 201
    
    @path_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_paths():
        """
        GET /api/path - Retrieve infinite scroll batch of sorted, filtered path documents.
        
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
        result = PathService.get_paths(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_paths Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @path_routes.route('/<path_id>', methods=['GET'])
    @handle_route_exceptions
    def get_path(path_id):
        """
        GET /api/path/<id> - Retrieve a specific path document by ID.
        
        Args:
            path_id: The path ID to retrieve
            
        Returns:
            JSON response with the path document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        path = PathService.get_path(path_id, token, breadcrumb)
        logger.info(f"get_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(path), 200
    
    @path_routes.route('/<path_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_path(path_id):
        """
        PATCH /api/path/<id> - Update a path document.
        
        Args:
            path_id: The path ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated path document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        path = PathService.update_path(path_id, data, token, breadcrumb)
        
        logger.info(f"update_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(path), 200
    
    logger.info("Path Flask Routes Registered")
    return path_routes