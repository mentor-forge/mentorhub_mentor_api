"""
Unit tests for Profile service (Mentor Dashboard, read-only).
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

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profiles_builds_dashboard(self, mock_get_mongo, mock_get_config):
        """Dashboard combines profile info, journey progress, and recent encounter."""
        mock_get_config.return_value = _make_config()

        def fake_get_documents(collection_name, match=None, project=None, sort_by=None):
            if collection_name == "Profile" and match == {"name": "mike"}:
                return [{"_id": MENTOR_ID, "name": "mike"}]
            if collection_name == "Profile" and match == {"mentor_id": MENTOR_ID}:
                return [
                    {"_id": MENTEE_1_ID, "name": "daniel", "description": "mentee one"},
                    {"_id": MENTEE_2_ID, "name": "lucky", "description": "mentee two"},
                ]
            if collection_name == "Journey":
                if match["profile_id"] == MENTEE_1_ID:
                    return [
                        {
                            "status": "active",
                            "library": [1, 2, 3],
                            "now": [1],
                            "next": [
                                {"resources": ["a", "b"]},
                                {"resources": ["c"]},
                            ],
                        }
                    ]
                return []
            if collection_name == "Encounter":
                if match["mentee_id"] == MENTEE_1_ID:
                    return [
                        {
                            "_id": ENCOUNTER_ID,
                            "date": "2025-02-01T00:00:00Z",
                            "tldr": "great session",
                            "summary": "covered async patterns",
                        }
                    ]
                return []
            return []

        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = fake_get_documents
        mock_get_mongo.return_value = mock_mongo

        result = ProfileService.get_profiles(self.mock_token, self.mock_breadcrumb)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        first = result[0]
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

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profiles_empty_when_no_mentees(self, mock_get_mongo, mock_get_config):
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

    @patch("src.services.profile_service.Config.get_instance")
    @patch("src.services.profile_service.MongoIO.get_instance")
    def test_get_profile_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific profile document."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "profile1",
        }
        mock_get_mongo.return_value = mock_mongo

        result = ProfileService.get_profile(
            "123", self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Profile", "123")

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
