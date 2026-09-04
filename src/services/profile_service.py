"""
Profile service for business logic and RBAC.

Inherits shared consume surface from api_utils.services.ProfileService.
Builds Mentor Dashboard and composite ProfileDetail / Properties hub for Mentor role.
"""

import logging
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound
from api_utils.services import ProfileService as SharedProfileService
from pymongo import ASCENDING

logger = logging.getLogger(__name__)


class ProfileService(SharedProfileService):
    """
    Service class for Profile domain operations.

    Inherits base consume operations from SharedProfileService.
    Implements Mentor Dashboard aggregation, composite ProfileDetail, and Properties hub.
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """
        Authorize an operation for the Profile domain.
        Requires mentor or admin role.
        """
        config = Config.get_instance()
        allowed_roles = {config.ROLE_MENTOR, config.ROLE_ADMIN}
        roles = token.get("roles", []) or []
        if not allowed_roles.intersection(roles):
            raise HTTPForbidden("Mentor or admin role required to access profile data")

    @classmethod
    def get_profile_by_token(cls, token, breadcrumb):
        """Resolve the caller's Profile from the JWT identity."""
        return super().get_profile_by_token(token, breadcrumb)

    @classmethod
    def get_profiles(
        cls,
        token,
        breadcrumb,
        offset=None,
        size=None,
        filters=None,
        sort_by=None,
    ):
        """Build the Mentor Dashboard for the current user."""
        cls._check_permission(token, "read")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()

        from src.services.journey_service import JourneyService
        from src.services.encounter_service import EncounterService

        mentor_profile_id = token.get("profile_id")
        mentor = (
            mongo.get_document(config.PROFILE_COLLECTION_NAME, str(mentor_profile_id))
            if mentor_profile_id
            else None
        )
        if not mentor:
            logger.info(
                f"No profile found for mentor profile '{mentor_profile_id}'; "
                "returning empty dashboard"
            )
            return []
        mentor_id = mentor["_id"]

        mentees = mongo.get_documents(
            config.PROFILE_COLLECTION_NAME,
            match={"mentor_id": mentor_id},
            sort_by=[("display_name", ASCENDING)],
        )

        dashboard = [
            {
                "_id": mentee["_id"],
                "name": mentee.get("display_name"),
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
            f"for profile {mentor_profile_id}"
        )
        return dashboard

    @classmethod
    def get_profile(cls, profile_id, token, breadcrumb):
        """Build the composite Profile detail view for a single mentee."""
        cls._check_permission(token, "read")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        profile = mongo.get_document(config.PROFILE_COLLECTION_NAME, profile_id)
        if profile is None:
            raise HTTPNotFound(f"Profile {profile_id} not found")

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

    @classmethod
    def _resource_ref(cls, value):
        """Normalize a journey resource reference to a string id or name."""
        if value is None:
            return None
        if isinstance(value, dict):
            if "resource_id" in value:
                return cls._resource_ref(value.get("resource_id"))
            if "$oid" in value:
                return str(value["$oid"])
            if "_id" in value:
                return str(value["_id"])
        return str(value)

    @classmethod
    def _load_resource(cls, mongo, config, resource_ref, cache):
        """Load a Resource by ObjectId or name, with an in-memory cache."""
        if not resource_ref:
            return None
        if resource_ref in cache:
            return cache[resource_ref]
        resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_ref)
        if resource is None:
            resources = mongo.get_documents(
                config.RESOURCE_COLLECTION_NAME,
                match={"name": resource_ref},
            )
            resource = resources[0] if resources else None
        cache[resource_ref] = resource
        return resource

    @classmethod
    def _mentor_history(cls, mongo, config, encounters):
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

    @classmethod
    def get_profile_properties(cls, profile_id, token, breadcrumb):
        """
        Aggregate mentee activity for the Properties hub view.

        Joins Profile, Journey, Resource, and Encounter data for a single mentee.
        """
        cls._check_permission(token, "read")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()

        profile = mongo.get_document(config.PROFILE_COLLECTION_NAME, profile_id)
        if profile is None:
            raise HTTPNotFound(f"Profile {profile_id} not found")

        from src.services.journey_service import JourneyService
        from src.services.encounter_service import EncounterService

        journeys = mongo.get_documents(
            config.JOURNEY_COLLECTION_NAME,
            match={"profile_id": profile_id, "status": "active"},
        )
        journey = journeys[0] if journeys else None
        progress = JourneyService.get_journey_progress(profile_id, token, breadcrumb)
        encounters = EncounterService.get_encounters_for_mentee(
            profile_id, token, breadcrumb
        )

        resource_cache = {}
        sites_and_links = []
        resource_usage = []
        celebrations = []
        seen_usage = set()

        def add_site(scope, entry, resource):
            resource_id = str(resource.get("_id") or cls._resource_ref(entry))
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
                resource_ref = cls._resource_ref(entry.get("resource_id"))
                resource = cls._load_resource(
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
                resource_ref = cls._resource_ref(entry.get("resource_id"))
                resource = cls._load_resource(
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
                    resource_ref = cls._resource_ref(resource_ref_raw)
                    resource = cls._load_resource(
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
            last_activity_at = encounters[0].get("date")
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
            "mentor_history": cls._mentor_history(mongo, config, encounters),
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
