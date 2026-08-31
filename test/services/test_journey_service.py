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
    mock_config.ROLE_MENTOR = "mentor"
    mock_config.ROLE_ADMIN = "admin"
    return mock_config


class TestJourneyService(unittest.TestCase):
    """Test cases for JourneyService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_mentor_token = {"user_id": "mike", "roles": ["mentor"]}
        self.mock_admin_token = {"user_id": "admin", "roles": ["admin"]}
        self.mock_user_token = {"user_id": "regular", "roles": ["user"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "mike",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    def test_inherited_methods_exist(self):
        """Assert inherited methods exist on the subclass."""
        self.assertTrue(callable(getattr(JourneyService, "get_journey", None)))
        self.assertTrue(callable(getattr(JourneyService, "get_journey_progress", None)))

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
            MENTEE_ID, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertEqual(result, {"library": 3, "now": 1, "next": 3})

        mock_mongo.get_documents.assert_called_once_with(
            "Journey", match={"profile_id": MENTEE_ID, "status": "active"}
        )

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_journey_progress_allowed_for_admin(
        self, mock_get_mongo, mock_get_config
    ):
        """Admin may call get_journey_progress."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.get_journey_progress(
            MENTEE_ID, self.mock_admin_token, self.mock_breadcrumb
        )
        self.assertEqual(result, {"library": 0, "now": 0, "next": 0})

    @patch("src.services.journey_service.Config.get_instance")
    def test_get_journey_progress_forbidden_without_mentor_or_admin(
        self, mock_get_config
    ):
        """Non-mentor cannot call get_journey_progress."""
        mock_get_config.return_value = _make_config()

        with self.assertRaises(HTTPForbidden):
            JourneyService.get_journey_progress(
                MENTEE_ID, self.mock_user_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
