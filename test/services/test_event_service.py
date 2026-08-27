"""
Unit tests for Event service.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.services.event_service import EventService
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestEventService(unittest.TestCase):
    """Test cases for EventService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_admin_token = {"user_id": "admin_user", "roles": ["admin"]}
        self.mock_mentor_token = {"user_id": "mentor_user", "roles": ["mentor"]}
        self.mock_user_token = {"user_id": "regular_user", "roles": ["user"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    def test_inherited_methods_exist(self):
        """Assert inherited methods exist on the subclass."""
        self.assertTrue(callable(getattr(EventService, "get_events", None)))

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_allowed_for_mentor(self, mock_get_mongo, mock_get_config):
        """Test mentor may create an event."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {
            "type": "login",
            "context": {"profile_id": "000000000000000000000001"},
        }
        event_id = EventService.create_event(
            data, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertEqual(event_id, "123")
        mock_mongo.create_document.assert_called_once()

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """Test admin may create an event."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"type": "login"}
        event_id = EventService.create_event(
            data, self.mock_admin_token, self.mock_breadcrumb
        )

        self.assertEqual(event_id, "123")

    @patch("src.services.event_service.Config.get_instance")
    def test_create_event_forbidden_without_mentor_or_admin(self, mock_get_config):
        """Test create raises HTTPForbidden without mentor/admin."""
        mock_config = MagicMock()
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        data = {"type": "login"}
        with self.assertRaises(HTTPForbidden):
            EventService.create_event(data, self.mock_user_token, self.mock_breadcrumb)

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "type": "login"}
        EventService.create_event(data, self.mock_mentor_token, self.mock_breadcrumb)

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test create_event raises HTTPInternalServerError on error."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("DB error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            EventService.create_event(
                {"type": "login"}, self.mock_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_get_event_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of an event."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "type": "login"}
        mock_get_mongo.return_value = mock_mongo

        event = EventService.get_event(
            "123", self.mock_mentor_token, self.mock_breadcrumb
        )
        self.assertEqual(event["_id"], "123")

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_get_event_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_event raises HTTPNotFound when document doesn't exist."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            EventService.get_event("999", self.mock_mentor_token, self.mock_breadcrumb)


if __name__ == "__main__":
    unittest.main()
