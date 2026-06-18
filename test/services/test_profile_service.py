"""
Unit tests for Profile service (Mentor Dashboard, read-only).

After L040 the Profile service composes its responses from dedicated domain
services: journey progress comes from ``JourneyService`` and encounter data from
``EncounterService``. These tests mock those collaborators and assert that
``ProfileService`` delegates correctly while keeping the dashboard and composite
response shapes unchanged.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.profile_service import ProfileService
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound

MENTOR_ID = ObjectId("507f1f77bcf86cd799439001")
MENTEE_1_ID = ObjectId("507f1f77bcf86cd799439011")
MENTEE_2_ID = ObjectId("507f1f77bcf86cd799439012")
ENCOUNTER_ID = ObjectId("507f1f77bcf86cd7994390aa")


def _make_config():
    mock_config = MagicMock()
    mock_config.PROFILE_COLLECTION_NAME = "Profile"
    mock_config.JOURNEY_COLLECTION_NAME = "Journey"
    mock_config.ENCOUNTER_COLLECTION_NAME = "Encounter"
    return mock_config


class TestProfileService(unittest.TestCase):
    """Test cases for ProfileService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "mike", "roles": ["mentor"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "mike",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.encounter_service.EncounterService.get_recent_encounter")
    @patch("src.services.journey_service.JourneyService.get_journey_progress")
    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profiles_builds_dashboard(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_journey_progress,
        mock_get_recent_encounter,
    ):
        """Dashboard combines profile info with delegated journey/encounter data."""
        mock_get_config.return_value = _make_config()

        def fake_get_documents(collection_name, match=None, project=None, sort_by=None):
            if collection_name == "Profile" and match == {"name": "mike"}:
                return [{"_id": MENTOR_ID, "name": "mike"}]
            if collection_name == "Profile" and match == {"mentor_id": MENTOR_ID}:
                return [
                    {"_id": MENTEE_1_ID, "name": "daniel", "description": "mentee one"},
                    {"_id": MENTEE_2_ID, "name": "lucky", "description": "mentee two"},
                ]
            return []

        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = fake_get_documents
        mock_get_mongo.return_value = mock_mongo

        def fake_journey_progress(profile_id, token, breadcrumb):
            if profile_id == MENTEE_1_ID:
                return {"library": 3, "now": 1, "next": 3}
            return {"library": 0, "now": 0, "next": 0}

        def fake_recent_encounter(mentee_id, token, breadcrumb):
            if mentee_id == MENTEE_1_ID:
                return {
                    "_id": ENCOUNTER_ID,
                    "date": "2025-02-01T00:00:00Z",
                    "tldr": "great session",
                    "summary": "covered async patterns",
                }
            return None

        mock_get_journey_progress.side_effect = fake_journey_progress
        mock_get_recent_encounter.side_effect = fake_recent_encounter

        result = ProfileService.get_profiles(self.mock_token, self.mock_breadcrumb)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        first = result[0]
        self.assertEqual(
            set(first.keys()),
            {
                "_id",
                "name",
                "description",
                "progress",
                "last_encounter",
            },
        )
        self.assertEqual(first["_id"], MENTEE_1_ID)
        self.assertEqual(first["name"], "daniel")
        self.assertEqual(first["description"], "mentee one")
        self.assertEqual(first["progress"], {"library": 3, "now": 1, "next": 3})
        self.assertEqual(first["last_encounter"]["_id"], ENCOUNTER_ID)
        self.assertEqual(first["last_encounter"]["summary"], "covered async patterns")

        second = result[1]
        self.assertEqual(second["name"], "lucky")
        self.assertEqual(second["progress"], {"library": 0, "now": 0, "next": 0})
        self.assertIsNone(second["last_encounter"])

        # Journey/encounter data is fetched via the dedicated services, once per
        # mentee, with the mentee Profile id and the caller's token/breadcrumb.
        mock_get_journey_progress.assert_any_call(
            MENTEE_1_ID, self.mock_token, self.mock_breadcrumb
        )
        mock_get_journey_progress.assert_any_call(
            MENTEE_2_ID, self.mock_token, self.mock_breadcrumb
        )
        self.assertEqual(mock_get_journey_progress.call_count, 2)
        mock_get_recent_encounter.assert_any_call(
            MENTEE_1_ID, self.mock_token, self.mock_breadcrumb
        )
        mock_get_recent_encounter.assert_any_call(
            MENTEE_2_ID, self.mock_token, self.mock_breadcrumb
        )
        self.assertEqual(mock_get_recent_encounter.call_count, 2)

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profiles_forbidden_without_mentor_role(
        self, mock_get_mongo, mock_get_config
    ):
        """Callers lacking the mentor role are denied before any DB access."""
        mock_get_config.return_value = _make_config()
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        non_mentor_token = {"user_id": "carol", "roles": ["coordinator"]}
        with self.assertRaises(HTTPForbidden):
            ProfileService.get_profiles(non_mentor_token, self.mock_breadcrumb)

        # RBAC must short-circuit before touching the database
        mock_mongo.get_documents.assert_not_called()

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profiles_empty_when_no_mentor_profile(
        self, mock_get_mongo, mock_get_config
    ):
        """Return an empty list when the caller has no Profile."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        result = ProfileService.get_profiles(self.mock_token, self.mock_breadcrumb)

        self.assertEqual(result, [])
        # Only the mentor lookup should have run
        mock_mongo.get_documents.assert_called_once_with(
            "Profile", match={"name": "mike"}
        )

    @patch("src.services.encounter_service.EncounterService.get_recent_encounter")
    @patch("src.services.journey_service.JourneyService.get_journey_progress")
    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profiles_empty_when_no_mentees(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_journey_progress,
        mock_get_recent_encounter,
    ):
        """Return an empty list when the mentor has no assigned mentees."""
        mock_get_config.return_value = _make_config()

        def fake_get_documents(collection_name, match=None, project=None, sort_by=None):
            if match == {"name": "mike"}:
                return [{"_id": MENTOR_ID, "name": "mike"}]
            return []

        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = fake_get_documents
        mock_get_mongo.return_value = mock_mongo

        result = ProfileService.get_profiles(self.mock_token, self.mock_breadcrumb)

        self.assertEqual(result, [])
        # No mentees means no delegation to the journey/encounter services.
        mock_get_journey_progress.assert_not_called()
        mock_get_recent_encounter.assert_not_called()

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profiles_propagates_unexpected_errors(
        self, mock_get_mongo, mock_get_config
    ):
        """Unexpected errors propagate untouched for the route wrapper to handle."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = RuntimeError("Database error")
        mock_get_mongo.return_value = mock_mongo

        # The service no longer rewraps into HTTPInternalServerError; the raw
        # error surfaces so handle_route_exceptions can produce the 500.
        with self.assertRaises(RuntimeError):
            ProfileService.get_profiles(self.mock_token, self.mock_breadcrumb)

    @patch("src.services.encounter_service.EncounterService.get_encounters_for_mentee")
    @patch("src.services.mentee_service.MenteeService.get_mentee")
    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profile_returns_composite(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_mentee,
        mock_get_encounters_for_mentee,
    ):
        """get_profile returns the {profile, mentee, encounters} composite."""
        mock_get_config.return_value = _make_config()

        profile_id = str(MENTEE_1_ID)
        profile_doc = {"_id": MENTEE_1_ID, "name": "daniel"}
        mentee_doc = {"_id": ObjectId("507f1f77bcf86cd7994390bb"), "notes": "n"}

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = profile_doc
        mock_get_mongo.return_value = mock_mongo

        mock_get_mentee.return_value = mentee_doc

        newer = {
            "_id": ENCOUNTER_ID,
            "mentee_id": MENTEE_1_ID,
            "date": "2025-03-01T00:00:00Z",
        }
        older = {
            "_id": ObjectId("507f1f77bcf86cd7994390a1"),
            "mentee_id": MENTEE_1_ID,
            "date": "2025-01-01T00:00:00Z",
        }
        # The Encounter service is responsible for filtering by mentee and
        # ordering most-recent-first; ProfileService passes the result through.
        mock_get_encounters_for_mentee.return_value = [newer, older]

        result = ProfileService.get_profile(
            profile_id, self.mock_token, self.mock_breadcrumb
        )

        # Composite shape matches the ProfileDetail contract exactly.
        self.assertEqual(set(result.keys()), {"profile", "mentee", "encounters"})
        self.assertEqual(result["profile"], profile_doc)
        self.assertEqual(result["mentee"], mentee_doc)
        self.assertEqual(
            [e["_id"] for e in result["encounters"]], [ENCOUNTER_ID, older["_id"]]
        )

        # The Profile is read directly; cross-collection data is not.
        mock_mongo.get_document.assert_called_once_with("Profile", profile_id)
        mock_mongo.get_documents.assert_not_called()

        # Related domains are fetched service-to-service.
        mock_get_mentee.assert_called_once_with(
            profile_id, self.mock_token, self.mock_breadcrumb
        )
        mock_get_encounters_for_mentee.assert_called_once_with(
            profile_id, self.mock_token, self.mock_breadcrumb
        )

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profile_forbidden_without_mentor_role(
        self, mock_get_mongo, mock_get_config
    ):
        """Single-profile reads also require the mentor role."""
        mock_get_config.return_value = _make_config()
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        non_mentor_token = {"user_id": "carol", "roles": []}
        with self.assertRaises(HTTPForbidden):
            ProfileService.get_profile("123", non_mentor_token, self.mock_breadcrumb)
        mock_mongo.get_document.assert_not_called()

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profile_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_profile raises HTTPNotFound when document not found."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            ProfileService.get_profile("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profile_propagates_unexpected_errors(
        self, mock_get_mongo, mock_get_config
    ):
        """Unexpected errors propagate untouched for the route wrapper to handle."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = RuntimeError("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(RuntimeError):
            ProfileService.get_profile("123", self.mock_token, self.mock_breadcrumb)

    def test_check_permission_allows_mentor(self):
        """A token with the mentor role passes the permission check."""
        ProfileService._check_permission(self.mock_token, "read")

    def test_check_permission_denies_non_mentor(self):
        """A token without the mentor role raises HTTPForbidden."""
        with self.assertRaises(HTTPForbidden):
            ProfileService._check_permission(
                {"user_id": "carol", "roles": ["coordinator"]}, "read"
            )


if __name__ == "__main__":
    unittest.main()
