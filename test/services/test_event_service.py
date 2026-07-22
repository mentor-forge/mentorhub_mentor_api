"""
Unit tests for Event service (create-style with create + read).
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.event_service import EventService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestEventService(unittest.TestCase):
    """Test cases for EventService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_success(self, mock_get_mongo, mock_get_config):
        """Test successful creation of a event document."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {
            "type": "login",
            "context": {"profile_id": "000000000000000000000001"},
        }

        event_id = EventService.create_event(
            data, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(event_id, "123")
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Event")
        created_data = call_args[0][1]
        self.assertIn("created", created_data)
        self.assertEqual(created_data["type"], "login")

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "type": "login"}

        EventService.create_event(data, self.mock_token, self.mock_breadcrumb)

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_uses_breadcrumb_directly(
        self, mock_get_mongo, mock_get_config
    ):
        """Test create_event uses breadcrumb directly for created field."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        breadcrumb = {
            "from_ip": "192.168.1.1",
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "correlation_id": "test-id",
        }

        result = EventService.create_event(
            {"type": "login"}, self.mock_token, breadcrumb
        )

        self.assertEqual(result, "123")
        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertEqual(created_data["created"], breadcrumb)
        self.assertEqual(created_data["created"]["from_ip"], "192.168.1.1")

    @patch("src.services.event_service.SharedEventService")
    def test_get_events_delegates_to_shared(self, mock_shared):
        """The Event list read delegates to the shared EventService."""
        mock_shared.get_events.return_value = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "type": "login"},
        ]

        sort_by = [("created.at_time", -1), ("_id", -1)]
        result = EventService.get_events(
            self.mock_token,
            self.mock_breadcrumb,
            offset=0,
            size=20,
            filters={"type": ["login"]},
            sort_by=sort_by,
            profile_id="507f1f77bcf86cd799439099",
        )

        self.assertEqual(len(result), 1)
        mock_shared.get_events.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            offset=0,
            size=20,
            filters={"type": ["login"]},
            sort_by=sort_by,
            profile_id="507f1f77bcf86cd799439099",
        )

    @patch("src.services.event_service.SharedEventService")
    def test_get_events_propagates_shared_errors(self, mock_shared):
        """Errors from the shared service surface unchanged."""
        mock_shared.get_events.side_effect = HTTPInternalServerError(
            "Failed to retrieve events"
        )
        with self.assertRaises(HTTPInternalServerError):
            EventService.get_events(self.mock_token, self.mock_breadcrumb)

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_get_event_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific event document."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "type": "login",
        }
        mock_get_mongo.return_value = mock_mongo

        result = EventService.get_event("123", self.mock_token, self.mock_breadcrumb)

        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Event", "123")

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_get_event_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_event raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            EventService.get_event("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test create_event handles database exceptions."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            EventService.create_event(
                {"type": "login"}, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_get_event_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_event handles database exceptions."""
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            EventService.get_event("123", self.mock_token, self.mock_breadcrumb)


if __name__ == "__main__":
    unittest.main()
