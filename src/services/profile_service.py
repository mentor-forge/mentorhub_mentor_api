"""
Profile service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for the Profile domain. The Profile
list endpoint powers the Mentor Dashboard: it returns the mentees assigned to
the current user along with each mentee's learning-journey progress and most
recent encounter summary.

Per the API standards (separation of concerns), this service contains business
logic only. It raises the appropriate domain exceptions (e.g. HTTPForbidden,
HTTPNotFound); the route layer's ``@handle_route_exceptions`` wrapper is
responsible for translating those, and any unexpected error, into HTTP
responses.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound
from pymongo import ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

# Role required to access Profile domain data through this service
MENTOR_ROLE = "mentor"


class ProfileService:
    """
    Service class for Profile domain operations.

    Handles:
    - RBAC authorization checks (requires the ``mentor`` role)
    - MongoDB operations via MongoIO singleton
    - Mentor Dashboard aggregation (Profile + Journey progress + recent Encounter)
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Authorize an operation for the Profile domain.

        Only users granted the ``mentor`` role may access profile data through
        this service.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read')

        Raises:
            HTTPForbidden: If the caller does not hold the ``mentor`` role
        """
        roles = token.get("roles", []) or []
        if MENTOR_ROLE not in roles:
            raise HTTPForbidden("Mentor role required to access profile data")

    @staticmethod
    def get_profiles(token, breadcrumb):
        """
        Build the Mentor Dashboard for the current user.

        The caller's Profile is resolved from the JWT identity (the token's
        ``user_id`` matches ``Profile.name``). One dashboard card is returned per
        mentee assigned to that mentor (Profiles whose ``mentor_id`` matches the
        caller's Profile ``_id``), in a pre-determined order (by name). This
        endpoint is read-only and non-paginated, so it takes no parameters.

        Each card contains:
        - basic Profile information (``_id``, ``name``, ``description``)
        - ``progress``: resource counts for the active Journey (library/now/next)
        - ``last_encounter``: summary of the most recent Encounter, or ``None``

        Args:
            token: Authentication token (``user_id`` identifies the mentor)
            breadcrumb: Audit breadcrumb

        Returns:
            list[dict]: Mentor Dashboard cards, one per mentee.

        Raises:
            HTTPForbidden: If the caller does not hold the ``mentor`` role
        """
        ProfileService._check_permission(token, "read")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()

        mentor_name = token.get("user_id")
        mentors = mongo.get_documents(
            config.PROFILE_COLLECTION_NAME,
            match={"name": mentor_name},
        )
        if not mentors:
            logger.info(
                f"No profile found for mentor '{mentor_name}'; "
                "returning empty dashboard"
            )
            return []
        mentor_id = mentors[0]["_id"]

        mentees = mongo.get_documents(
            config.PROFILE_COLLECTION_NAME,
            match={"mentor_id": mentor_id},
            sort_by=[("name", ASCENDING)],
        )

        dashboard = [
            {
                "_id": mentee["_id"],
                "name": mentee.get("name"),
                "description": mentee.get("description"),
                "progress": ProfileService._journey_progress(
                    mongo, config, mentee["_id"]
                ),
                "last_encounter": ProfileService._recent_encounter(
                    mongo, config, mentee["_id"]
                ),
            }
            for mentee in mentees
        ]

        logger.info(
            f"Built mentor dashboard with {len(dashboard)} mentees "
            f"for user {mentor_name}"
        )
        return dashboard

    @staticmethod
    def _journey_progress(mongo, config, profile_id):
        """
        Count the resources in the mentee's active Learning Journey by scope.

        Returns a dict with ``library``, ``now``, and ``next`` counts. ``library``
        and ``now`` count their resource entries directly; ``next`` sums the
        resource entries across all Next topics. Returns zeros when the mentee
        has no active journey.
        """
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

    @staticmethod
    def _recent_encounter(mongo, config, profile_id):
        """
        Return a summary of the mentee's most recent Encounter, or ``None``.

        The most recent encounter is the one with the latest ``date``.
        """
        encounters = mongo.get_documents(
            config.ENCOUNTER_COLLECTION_NAME,
            match={"mentee_id": profile_id},
            sort_by=[("date", DESCENDING)],
        )
        if not encounters:
            return None

        encounter = encounters[0]
        return {
            "_id": encounter["_id"],
            "date": encounter.get("date"),
            "tldr": encounter.get("tldr"),
            "summary": encounter.get("summary"),
        }

    @staticmethod
    def get_profile(profile_id, token, breadcrumb):
        """
        Build the composite Profile detail view for a single mentee.

        Returns the ``ProfileDetail`` document defined by the OpenAPI contract:
        the mentee's ``Profile`` plus the related mentee-notes document and the
        full list of the mentee's ``Encounter`` documents. The related domains
        are assembled with **service-to-service** calls (``MenteeService`` and
        ``EncounterService``); this service never reads the Mentee/Encounter
        collections directly for the composite.

        Args:
            profile_id: The mentee Profile ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: ``{"profile": ..., "mentee": ..., "encounters": [...]}``

        Raises:
            HTTPForbidden: If the caller does not hold the ``mentor`` role
            HTTPNotFound: If the Profile is not found
        """
        ProfileService._check_permission(token, "read")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        profile = mongo.get_document(config.PROFILE_COLLECTION_NAME, profile_id)
        if profile is None:
            raise HTTPNotFound(f"Profile {profile_id} not found")

        # Imported lazily so the Mentee/Encounter services (which do not import
        # ProfileService) never create an import cycle.
        from src.services.mentee_service import MenteeService

        mentee = MenteeService.get_mentee(profile_id, token, breadcrumb)
        encounters = ProfileService._mentee_encounters(profile_id, token, breadcrumb)

        logger.info(
            f"Built profile detail for {profile_id} with {len(encounters)} "
            f"encounters for user {token.get('user_id')}"
        )
        return {"profile": profile, "mentee": mentee, "encounters": encounters}

    @staticmethod
    def _mentee_encounters(profile_id, token, breadcrumb):
        """
        Fetch a mentee's Encounters through the Encounter service.

        Cross-collection reads must go through the owning service, so this asks
        ``EncounterService`` for encounters and keeps the ones linked to this
        mentee (``Encounter.mentee_id`` is the mentee's Profile id), most-recent
        first. ``EncounterService`` only exposes the shared list reader today;
        L040 moves a dedicated per-mentee read (and the recent-encounter logic)
        into ``EncounterService``.

        Args:
            profile_id: The mentee Profile id whose encounters are wanted
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            list[dict]: The mentee's Encounter documents, most recent first.
        """
        from src.services.encounter_service import EncounterService

        result = EncounterService.get_encounters(token, breadcrumb, limit=100)
        items = result.get("items", []) if isinstance(result, dict) else (result or [])

        mine = [e for e in items if str(e.get("mentee_id")) == str(profile_id)]
        mine.sort(key=lambda e: e.get("date") or "", reverse=True)
        return mine
