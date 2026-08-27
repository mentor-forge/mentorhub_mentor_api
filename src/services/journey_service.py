"""
Journey service for business logic and RBAC.

Inherits shared read helpers from api_utils.services.JourneyService.
Provides get_journey_progress for Mentor Dashboard.
"""

import logging
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPForbidden
from api_utils.services import JourneyService as SharedJourneyService

logger = logging.getLogger(__name__)


class JourneyService(SharedJourneyService):
    """
    Service class for Learning Journey domain operations.

    Inherits base Journey domain methods from SharedJourneyService.
    Provides get_journey_progress for dashboard reporting.
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """Authorize an operation for the Journey domain."""
        config = Config.get_instance()
        allowed_roles = {config.ROLE_MENTOR, config.ROLE_ADMIN}
        roles = token.get("roles", []) or []
        if not allowed_roles.intersection(roles):
            raise HTTPForbidden("Mentor or admin role required to access journey data")

    @classmethod
    def get_journey_progress(cls, profile_id, token, breadcrumb):
        """Count the resources in a mentee's active Learning Journey by scope."""
        cls._check_permission(token, "read")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()

        journeys = mongo.get_documents(
            config.JOURNEY_COLLECTION_NAME,
            match={"profile_id": profile_id, "status": "active"},
        )
        if not journeys:
            return {"library": 0, "now": 0, "next": 0}

        journey = journeys[0]
        next_resources = sum(
            len(topic.get("resources") or []) for topic in (journey.get("next") or [])
        )
        return {
            "library": len(journey.get("library") or []),
            "now": len(journey.get("now") or []),
            "next": next_resources,
        }
