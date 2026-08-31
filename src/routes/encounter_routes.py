"""
Encounter routes for Flask API.

Provides endpoints for Encounter domain:
- POST /api/encounter - Create a new encounter document
- GET /api/encounter - Get encounters for mentee (?mentee_id=...)
- GET /api/encounter/<id> - Get a specific encounter document by ID
- PATCH /api/encounter/<id> - Update an encounter document
"""

import logging
from flask import jsonify, request
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from api_utils.routes.shared_get_routes import create_encounter_get_routes
from src.services.encounter_service import EncounterService

logger = logging.getLogger(__name__)


def create_encounter_routes():
    """
    Create a Flask Blueprint exposing encounter endpoints.

    GET operations (list with ?mentee_id= and by-id) are mounted via
    create_encounter_get_routes(EncounterService).
    Control POST and PATCH are added locally.
    """
    bp = create_encounter_get_routes(EncounterService, name="encounter_routes")

    @bp.route("", methods=["POST"])
    @handle_route_exceptions
    def create_encounter():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        encounter_id = EncounterService.create_encounter(data, token, breadcrumb)
        encounter = EncounterService.get_encounter(encounter_id, token, breadcrumb)

        logger.info(
            f"create_encounter Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(encounter), 201

    @bp.route("/<encounter_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_encounter(encounter_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        updated_encounter = EncounterService.update_encounter(
            encounter_id, data, token, breadcrumb
        )

        logger.info(
            f"update_encounter Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(updated_encounter), 200

    return bp
