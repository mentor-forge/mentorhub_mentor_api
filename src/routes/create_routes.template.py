"""
{{item}} routes for Flask API.

Provides endpoints for Create domain:
- POST /api/{{item | lower}} - Create a new {{item | lower}} document
- GET /api/{{item | lower}} - Get all {{item | lower}} documents
- GET /api/{{item | lower}}/<id> - Get a specific {{item | lower}} document by ID
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.{{item | lower}}_service import {{item}}Service

import logging
logger = logging.getLogger(__name__)


def create_{{item | lower}}_routes():
    """
    Create a Flask Blueprint exposing {{item | lower}} endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with {{item | lower}} routes
    """
    {{item | lower}}_routes = Blueprint('{{item | lower}}_routes', __name__)
    
    @{{item | lower}}_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_{{item | lower}}():
        """
        POST /api/{{item | lower}} - Create a new {{item | lower}} document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the {{item | lower}}d {{item | lower}} document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        {{item | lower}}_id = {{item}}Service.create_{{item | lower}}(data, token, breadcrumb)
        {{item | lower}} = {{item}}Service.get_{{item | lower}}({{item | lower}}_id, token, breadcrumb)
        
        logger.info(f"create_{{item | lower}} Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify({{item | lower}}), 201
    
    @{{item | lower}}_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_{{item | lower}}s():
        """
        GET /api/{{item | lower}} - Retrieve infinite scroll batch of sorted, filtered {{item | lower}} documents.
        
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
        result = {{item}}Service.get_{{item | lower}}s(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_{{item | lower}}s Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @{{item | lower}}_routes.route('/<{{item | lower}}_id>', methods=['GET'])
    @handle_route_exceptions
    def get_{{item | lower}}({{item | lower}}_id):
        """
        GET /api/{{item | lower}}/<id> - Retrieve a specific {{item | lower}} document by ID.
        
        Args:
            {{item | lower}}_id: The {{item | lower}} ID to retrieve
            
        Returns:
            JSON response with the {{item | lower}} document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        {{item | lower}} = {{item}}Service.get_{{item | lower}}({{item | lower}}_id, token, breadcrumb)
        logger.info(f"get_{{item | lower}} Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify({{item | lower}}), 200
    
    logger.info("Create Flask Routes Registered")
    return {{item | lower}}_routes
