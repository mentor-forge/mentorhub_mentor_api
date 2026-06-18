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
from pymongo import ASCENDING
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

        # Imported lazily so the Journey/Encounter services (which do not import
        # ProfileService) never create an import cycle.
        from src.services.journey_service import JourneyService
        from src.services.encounter_service import EncounterService

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
                "progress": JourneyService.get_journey_progress(
                    mentee["_id"], token, breadcrumb
                ),
                "last_encounter": EncounterService.get_recent_encounter(
                    mentee["_id"], token, breadcrumb
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
        from src.services.encounter_service import EncounterService

        mentee = MenteeService.get_mentee(profile_id, token, breadcrumb)
        encounters = EncounterService.get_encounters_for_mentee(
            profile_id, token, breadcrumb
        )

        logger.info(
            f"Built profile detail for {profile_id} with {len(encounters)} "
            f"encounters for user {token.get('user_id')}"
        )
        return {"profile": profile, "mentee": mentee, "encounters": encounters}
