"""
Encounter routes for Flask API.

Provides endpoints for Encounter domain:
- POST /api/encounter - Create a new encounter document
- GET /api/encounter - Get all encounter documents (with optional ?name= query parameter)
- GET /api/encounter/<id> - Get a specific encounter document by ID
- PATCH /api/encounter/<id> - Update a encounter document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.encounter_service import EncounterService

import logging
logger = logging.getLogger(__name__)


def create_encounter_routes():
    """
    Create a Flask Blueprint exposing encounter endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with encounter routes
    """
    encounter_routes = Blueprint('encounter_routes', __name__)
    
    @encounter_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_encounter():
        """
        POST /api/encounter - Create a new encounter document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created encounter document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        encounter_id = EncounterService.create_encounter(data, token, breadcrumb)
        encounter = EncounterService.get_encounter(encounter_id, token, breadcrumb)
        
        logger.info(f"create_encounter Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(encounter), 201
    
    @encounter_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_encounters():
        """
        GET /api/encounter - Retrieve infinite scroll batch of sorted, filtered encounter documents.
        
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
        result = EncounterService.get_encounters(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_encounters Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @encounter_routes.route('/<encounter_id>', methods=['GET'])
    @handle_route_exceptions
    def get_encounter(encounter_id):
        """
        GET /api/encounter/<id> - Retrieve a specific encounter document by ID.
        
        Args:
            encounter_id: The encounter ID to retrieve
            
        Returns:
            JSON response with the encounter document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        encounter = EncounterService.get_encounter(encounter_id, token, breadcrumb)
        logger.info(f"get_encounter Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(encounter), 200
    
    @encounter_routes.route('/<encounter_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_encounter(encounter_id):
        """
        PATCH /api/encounter/<id> - Update a encounter document.
        
        Args:
            encounter_id: The encounter ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated encounter document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        encounter = EncounterService.update_encounter(encounter_id, data, token, breadcrumb)
        
        logger.info(f"update_encounter Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(encounter), 200
    
    logger.info("Encounter Flask Routes Registered")
    return encounter_routes