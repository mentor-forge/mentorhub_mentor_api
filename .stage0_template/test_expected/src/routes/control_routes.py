"""
Control routes for Flask API.

Provides endpoints for Control domain:
- POST /api/control - Create a new control document
- GET /api/control - Get all control documents (with optional ?name= query parameter)
- GET /api/control/<id> - Get a specific control document by ID
- PATCH /api/control/<id> - Update a control document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.control_service import ControlService

import logging
logger = logging.getLogger(__name__)


def create_control_routes():
    """
    Create a Flask Blueprint exposing control endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with control routes
    """
    control_routes = Blueprint('control_routes', __name__)
    
    @control_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_control():
        """
        POST /api/control - Create a new control document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created control document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        control_id = ControlService.create_control(data, token, breadcrumb)
        control = ControlService.get_control(control_id, token, breadcrumb)
        
        logger.info(f"create_control Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(control), 201
    
    @control_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_controls():
        """
        GET /api/control - Retrieve infinite scroll batch of sorted, filtered control documents.
        
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
        result = ControlService.get_controls(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_controls Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @control_routes.route('/<control_id>', methods=['GET'])
    @handle_route_exceptions
    def get_control(control_id):
        """
        GET /api/control/<id> - Retrieve a specific control document by ID.
        
        Args:
            control_id: The control ID to retrieve
            
        Returns:
            JSON response with the control document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        control = ControlService.get_control(control_id, token, breadcrumb)
        logger.info(f"get_control Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(control), 200
    
    @control_routes.route('/<control_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_control(control_id):
        """
        PATCH /api/control/<id> - Update a control document.
        
        Args:
            control_id: The control ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated control document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        control = ControlService.update_control(control_id, data, token, breadcrumb)
        
        logger.info(f"update_control Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(control), 200
    
    logger.info("Control Flask Routes Registered")
    return control_routes