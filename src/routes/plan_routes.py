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
        GET /api/plan - Retrieve all plan documents, sorted alphabetically by name.
        
        No query parameters: the list always returns every plan, sorted by
        name ascending (no search, pagination, or infinite scroll).
        
        Returns:
            JSON array of plan documents
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        result = PlanService.get_plans(token, breadcrumb)
        
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