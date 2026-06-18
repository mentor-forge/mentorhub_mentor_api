"""
Unit tests for Journey service (active-journey resource counts by scope).
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.journey_service import JourneyService
from api_utils.flask_utils.exceptions import HTTPForbidden

MENTEE_ID = ObjectId("507f1f77bcf86cd799439011")


def _make_config():
    mock_config = MagicMock()
    mock_config.JOURNEY_COLLECTION_NAME = "Journey"
    return mock_config


class TestJourneyService(unittest.TestCase):
    """Test cases for JourneyService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "mike", "roles": ["mentor"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "mike",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_journey_progress_counts_by_scope(
        self, mock_get_mongo, mock_get_config
    ):
        """Counts library/now directly and sums resources across next topics."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
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
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.get_journey_progress(
            MENTEE_ID, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result, {"library": 3, "now": 1, "next": 3})

        # Only the active journey for this mentee is queried.
        mock_mongo.get_documents.assert_called_once_with(
            "Journey", match={"profile_id": MENTEE_ID, "status": "active"}
        )

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_journey_progress_no_active_journey(
        self, mock_get_mongo, mock_get_config
    ):
        """Return zero counts when the mentee has no active journey."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.get_journey_progress(
            MENTEE_ID, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result, {"library": 0, "now": 0, "next": 0})

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_journey_progress_handles_missing_scope_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Missing/None scope fields are treated as empty (zero counts)."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {"status": "active", "library": None, "next": None}
        ]
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.get_journey_progress(
            MENTEE_ID, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result, {"library": 0, "now": 0, "next": 0})

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_journey_progress_forbidden_without_mentor_role(
        self, mock_get_mongo, mock_get_config
    ):
        """Callers lacking the mentor role are denied before any DB access."""
        mock_get_config.return_value = _make_config()
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        non_mentor_token = {"user_id": "carol", "roles": ["coordinator"]}
        with self.assertRaises(HTTPForbidden):
            JourneyService.get_journey_progress(
                MENTEE_ID, non_mentor_token, self.mock_breadcrumb
            )

        # RBAC must short-circuit before touching the database
        mock_mongo.get_documents.assert_not_called()

    def test_check_permission_allows_mentor(self):
        """A token with the mentor role passes the permission check."""
        JourneyService._check_permission(self.mock_token, "read")

    def test_check_permission_denies_non_mentor(self):
        """A token without the mentor role raises HTTPForbidden."""
        with self.assertRaises(HTTPForbidden):
            JourneyService._check_permission(
                {"user_id": "carol", "roles": ["coordinator"]}, "read"
            )


if __name__ == "__main__":
    unittest.main()
