"""
Profile service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for the Profile domain. The Profile
list endpoint powers the Mentor Dashboard: it returns the mentees assigned to
the current user along with each mentee's learning-journey progress and most
recent encounter summary.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPUnauthorized,
    HTTPInternalServerError,
)
from pymongo import ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

# HTTP exceptions that must propagate untouched to the route error handler
_HTTP_EXCEPTIONS = (HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPUnauthorized)


class ProfileService:
    """
    Service class for Profile domain operations.

    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Mentor Dashboard aggregation (Profile + Journey progress + recent Encounter)
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read')

        Raises:
            HTTPForbidden: If user doesn't have required permission

        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).
        """
        pass

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
        """
        try:
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
        except _HTTP_EXCEPTIONS:
            raise
        except Exception as e:
            logger.error(f"Error building mentor dashboard: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve profiles")

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
        Retrieve a specific profile document by ID.

        Args:
            profile_id: The profile ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The profile document

        Raises:
            HTTPNotFound: If profile is not found
        """
        try:
            ProfileService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            profile = mongo.get_document(config.PROFILE_COLLECTION_NAME, profile_id)
            if profile is None:
                raise HTTPNotFound(f"Profile { profile_id} not found")

            logger.info(
                f"Retrieved profile { profile_id} for user {token.get('user_id')}"
            )
            return profile
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving profile { profile_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve profile { profile_id}")
