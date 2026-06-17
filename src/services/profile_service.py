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
        Retrieve a specific profile document by ID.

        Args:
            profile_id: The profile ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The profile document

        Raises:
            HTTPForbidden: If the caller does not hold the ``mentor`` role
            HTTPNotFound: If profile is not found
        """
        ProfileService._check_permission(token, "read")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        profile = mongo.get_document(config.PROFILE_COLLECTION_NAME, profile_id)
        if profile is None:
            raise HTTPNotFound(f"Profile {profile_id} not found")

        logger.info(f"Retrieved profile {profile_id} for user {token.get('user_id')}")
        return profile

    @staticmethod
    def _resource_ref(value):
        """Normalize a journey resource reference to a string id or name."""
        if value is None:
            return None
        if isinstance(value, dict):
            if "resource_id" in value:
                return ProfileService._resource_ref(value.get("resource_id"))
            if "$oid" in value:
                return str(value["$oid"])
            if "_id" in value:
                return str(value["_id"])
        return str(value)

    @staticmethod
    def _load_resource(mongo, config, resource_ref, cache):
        """Load a Resource by ObjectId or name, with an in-memory cache."""
        if not resource_ref:
            return None
        if resource_ref in cache:
            return cache[resource_ref]
        resource = mongo.get_document(
            config.RESOURCE_COLLECTION_NAME, resource_ref
        )
        if resource is None:
            resources = mongo.get_documents(
                config.RESOURCE_COLLECTION_NAME,
                match={"name": resource_ref},
            )
            resource = resources[0] if resources else None
        cache[resource_ref] = resource
        return resource

    @staticmethod
    def _mentor_history(mongo, config, profile_id, encounters):
        """Build mentor history from encounters for a mentee."""
        history = {}
        for encounter in encounters:
            mentor_id = encounter.get("mentor_id")
            if not mentor_id:
                continue
            mentor_key = str(mentor_id)
            entry = history.setdefault(
                mentor_key,
                {
                    "mentor_id": mentor_key,
                    "mentor_name": None,
                    "encounter_count": 0,
                    "first_date": encounter.get("date"),
                    "last_date": encounter.get("date"),
                },
            )
            entry["encounter_count"] += 1
            encounter_date = encounter.get("date")
            if encounter_date:
                if not entry["first_date"] or encounter_date < entry["first_date"]:
                    entry["first_date"] = encounter_date
                if not entry["last_date"] or encounter_date > entry["last_date"]:
                    entry["last_date"] = encounter_date

        for entry in history.values():
            mentor = mongo.get_document(
                config.PROFILE_COLLECTION_NAME, entry["mentor_id"]
            )
            if mentor:
                entry["mentor_name"] = mentor.get("name")

        return sorted(
            history.values(),
            key=lambda item: item.get("last_date") or "",
            reverse=True,
        )

    @staticmethod
    def get_profile_properties(profile_id, token, breadcrumb):
        """
        Aggregate mentee activity for the Properties hub view.

        Joins Profile, Journey, Resource, and Encounter data for a single mentee.
        """
        ProfileService._check_permission(token, "read")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()

        profile = mongo.get_document(config.PROFILE_COLLECTION_NAME, profile_id)
        if profile is None:
            raise HTTPNotFound(f"Profile {profile_id} not found")

        journeys = mongo.get_documents(
            config.JOURNEY_COLLECTION_NAME,
            match={"profile_id": profile_id, "status": "active"},
        )
        journey = journeys[0] if journeys else None
        progress = ProfileService._journey_progress(mongo, config, profile_id)

        encounters = mongo.get_documents(
            config.ENCOUNTER_COLLECTION_NAME,
            match={"mentee_id": profile_id},
            sort_by=[("date", ASCENDING)],
        )

        resource_cache = {}
        sites_and_links = []
        resource_usage = []
        celebrations = []
        seen_usage = set()

        def add_site(scope, entry, resource):
            resource_id = str(resource.get("_id") or ProfileService._resource_ref(entry))
            sites_and_links.append(
                {
                    "resource_id": resource_id,
                    "name": resource.get("name") or resource_id,
                    "url": resource.get("url"),
                    "scope": scope,
                    "used": entry.get("used"),
                    "started": entry.get("started"),
                    "completed": entry.get("completed"),
                }
            )

        def add_usage(resource, times_used, status):
            resource_id = str(resource.get("_id"))
            if resource_id in seen_usage:
                return
            seen_usage.add(resource_id)
            resource_usage.append(
                {
                    "resource_id": resource_id,
                    "name": resource.get("name") or resource_id,
                    "times_used": times_used,
                    "status": status,
                }
            )

        if journey:
            for entry in journey.get("library") or []:
                resource_ref = ProfileService._resource_ref(entry.get("resource_id"))
                resource = ProfileService._load_resource(
                    mongo, config, resource_ref, resource_cache
                )
                if not resource:
                    continue
                add_site("library", entry, resource)
                add_usage(resource, 1, "completed")
                if entry.get("completed"):
                    celebrations.append(
                        {
                            "resource_id": str(resource.get("_id")),
                            "name": resource.get("name") or resource_ref,
                            "completed_at": entry.get("completed"),
                        }
                    )

            for entry in journey.get("now") or []:
                resource_ref = ProfileService._resource_ref(entry.get("resource_id"))
                resource = ProfileService._load_resource(
                    mongo, config, resource_ref, resource_cache
                )
                if not resource:
                    continue
                add_site("now", entry, resource)
                add_usage(
                    resource,
                    int(entry.get("used") or 0) or 1,
                    "in_progress",
                )

            for topic in journey.get("next") or []:
                for resource_ref_raw in topic.get("resources") or []:
                    resource_ref = ProfileService._resource_ref(resource_ref_raw)
                    resource = ProfileService._load_resource(
                        mongo, config, resource_ref, resource_cache
                    )
                    if not resource:
                        continue
                    add_site("next", {}, resource)
                    add_usage(resource, 0, "queued")

        celebrations.sort(
            key=lambda item: item.get("completed_at") or "",
            reverse=True,
        )

        last_activity_at = None
        if encounters:
            last_activity_at = encounters[-1].get("date")
        for celebration in celebrations:
            completed_at = celebration.get("completed_at")
            if completed_at and (
                not last_activity_at or completed_at > last_activity_at
            ):
                last_activity_at = completed_at

        result = {
            "profile": profile,
            "status_summary": {
                "profile_status": profile.get("status"),
                "journey_status": journey.get("status") if journey else None,
                "library_count": progress["library"],
                "now_count": progress["now"],
                "next_count": progress["next"],
                "encounters_count": len(encounters),
                "resources_engaged": len(seen_usage),
                "last_activity_at": last_activity_at,
            },
            "sites_and_links": sites_and_links,
            "mentor_history": ProfileService._mentor_history(
                mongo, config, profile_id, encounters
            ),
            "journey": journey,
            "path": None,
            "resource_usage": resource_usage,
            "celebrations": celebrations,
        }

        logger.info(
            f"Built profile properties for {profile_id} "
            f"for user {token.get('user_id')}"
        )
        return result
