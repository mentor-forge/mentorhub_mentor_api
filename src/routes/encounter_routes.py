"""
Encounter routes for Flask API.

Provides endpoints for Encounter domain:
- POST /api/encounter - Create a new encounter document
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
    encounter_routes = Blueprint("encounter_routes", __name__)

    @encounter_routes.route("", methods=["POST"])
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

        logger.info(
            f"create_encounter Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(encounter), 201

    @encounter_routes.route("/<encounter_id>", methods=["GET"])
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
        logger.info(
            f"get_encounter Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(encounter), 200

    @encounter_routes.route("/<encounter_id>", methods=["PATCH"])
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
        encounter = EncounterService.update_encounter(
            encounter_id, data, token, breadcrumb
        )

        logger.info(
            f"update_encounter Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(encounter), 200

    logger.info("Encounter Flask Routes Registered")
    return encounter_routes
