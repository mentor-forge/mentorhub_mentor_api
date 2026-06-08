"""
Plan routes for Flask API.

Provides endpoints for Plan domain:
- POST /api/plan - Create a new plan document
- GET /api/plan - Get all plan documents (with optional ?name= query parameter)
- GET /api/plan/<id> - Get a specific plan document by ID
- PATCH /api/plan/<id> - Update a plan document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.plan_service import PlanService

import logging
logger = logging.getLogger(__name__)


def create_plan_routes():
    """
    Create a Flask Blueprint exposing plan endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with plan routes
    """
    plan_routes = Blueprint('plan_routes', __name__)
    
    @plan_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_plan():
        """
        POST /api/plan - Create a new plan document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created plan document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        plan_id = PlanService.create_plan(data, token, breadcrumb)
        plan = PlanService.get_plan(plan_id, token, breadcrumb)
        
        logger.info(f"create_plan Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(plan), 201
    
    @plan_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_plans():
        """
        GET /api/plan - Retrieve infinite scroll batch of sorted, filtered plan documents.
        
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
        result = PlanService.get_plans(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_plans Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @plan_routes.route('/<plan_id>', methods=['GET'])
    @handle_route_exceptions
    def get_plan(plan_id):
        """
        GET /api/plan/<id> - Retrieve a specific plan document by ID.
        
        Args:
            plan_id: The plan ID to retrieve
            
        Returns:
            JSON response with the plan document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        plan = PlanService.get_plan(plan_id, token, breadcrumb)
        logger.info(f"get_plan Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(plan), 200
    
    @plan_routes.route('/<plan_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_plan(plan_id):
        """
        PATCH /api/plan/<id> - Update a plan document.
        
        Args:
            plan_id: The plan ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated plan document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        plan = PlanService.update_plan(plan_id, data, token, breadcrumb)
        
        logger.info(f"update_plan Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(plan), 200
    
    logger.info("Plan Flask Routes Registered")
    return plan_routes