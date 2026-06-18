"""
Journey service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for the Learning Journey domain. A
Journey document tracks a mentee's resources across three scopes: ``library``
(the full backlog), ``now`` (the current focus), and ``next`` (upcoming topics,
each holding its own resource list). The Mentor Dashboard reports the active
journey's resource counts per scope.

Per the API standards (separation of concerns), this service contains business
logic only. It raises the appropriate domain exceptions (e.g. HTTPForbidden);
the route layer's ``@handle_route_exceptions`` wrapper is responsible for
translating those, and any unexpected error, into HTTP responses.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPForbidden
import logging

logger = logging.getLogger(__name__)

# Role required to access Journey domain data through this service. Mirrors the
# mentor-facing permission pattern used by ProfileService. Adopting shared
# Config role constants is handled later in L050.
MENTOR_ROLE = "mentor"


class JourneyService:
    """
    Service class for Learning Journey domain operations.

    Handles:
    - RBAC authorization checks (requires the ``mentor`` role)
    - MongoDB operations via MongoIO singleton
    - Active-journey resource-count aggregation by scope (library/now/next)
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Authorize an operation for the Journey domain.

        Only users granted the ``mentor`` role may access journey data through
        this service.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read')

        Raises:
            HTTPForbidden: If the caller does not hold the ``mentor`` role
        """
        roles = token.get("roles", []) or []
        if MENTOR_ROLE not in roles:
            raise HTTPForbidden("Mentor role required to access journey data")

    @staticmethod
    def get_journey_progress(profile_id, token, breadcrumb):
        """
        Count the resources in a mentee's active Learning Journey by scope.

        Returns a dict with ``library``, ``now``, and ``next`` counts. ``library``
        and ``now`` count their resource entries directly; ``next`` sums the
        resource entries across all Next topics. Returns zeros when the mentee
        has no active journey.

        Args:
            profile_id: The mentee Profile id whose journey progress is wanted
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for audit/logging

        Returns:
            dict: ``{"library": int, "now": int, "next": int}``

        Raises:
            HTTPForbidden: If the caller does not hold the ``mentor`` role
        """
        JourneyService._check_permission(token, "read")

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
