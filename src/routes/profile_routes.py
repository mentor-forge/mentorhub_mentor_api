"""
Profile routes for Flask API.

Provides endpoints for Profile domain:
- GET /api/profile - Get all profile documents
- GET /api/profile/<id> - Get a specific profile document by ID
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.profile_service import ProfileService

import logging
logger = logging.getLogger(__name__)


def create_profile_routes():
    """
    Create a Flask Blueprint exposing profile endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with profile routes
    """
    profile_routes = Blueprint('profile_routes', __name__)
    
    @profile_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_profiles():
        """
        GET /api/profile - Retrieve infinite scroll batch of sorted, filtered profile documents.
        
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
        result = ProfileService.get_profiles(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_profiles Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @profile_routes.route('/<profile_id>', methods=['GET'])
    @handle_route_exceptions
    def get_profile(profile_id):
        """
        GET /api/profile/<id> - Retrieve a specific profile document by ID.
        
        Args:
            profile_id: The profile ID to retrieve
            
        Returns:
            JSON response with the profile document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        profile = ProfileService.get_profile(profile_id, token, breadcrumb)
        logger.info(f"get_profile Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(profile), 200
    
    logger.info("Profile Flask Routes Registered")
    return profile_routes