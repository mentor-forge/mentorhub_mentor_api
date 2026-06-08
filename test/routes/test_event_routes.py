"""
Unit tests for Event routes (create-style with POST and GET).
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.event_routes import create_event_routes


class TestEventRoutes(unittest.TestCase):
    """Test cases for Event routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_event_routes(),
            url_prefix="/api/event",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.event_routes.create_flask_token")
    @patch("src.routes.event_routes.create_flask_breadcrumb")
    @patch("src.routes.event_routes.EventService.create_event")
    @patch("src.routes.event_routes.EventService.get_event")
    def test_create_event_success(
        self,
        mock_get_event,
        mock_create_event,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/event for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_event.return_value = "123"
        mock_get_event.return_value = {
            "_id": "123",
            "name": "test-event",
            "status": "active",
        }

        response = self.client.post(
            "/api/event",
            json={"name": "test-event", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_event.assert_called_once()
        mock_get_event.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.event_routes.create_flask_token")
    @patch("src.routes.event_routes.create_flask_breadcrumb")
    @patch("src.routes.event_routes.EventService.get_events")
    def test_get_events_success(
        self,
        mock_get_events,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/event for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_events.return_value = {
            "items": [
                {"_id": "123", "name": "event1"},
                {"_id": "456", "name": "event2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/event")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_events.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.event_routes.create_flask_token")
    @patch("src.routes.event_routes.create_flask_breadcrumb")
    @patch("src.routes.event_routes.EventService.get_event")
    def test_get_event_success(
        self,
        mock_get_event,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/event/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_event.return_value = {
            "_id": "123",
            "name": "event1",
        }

        response = self.client.get("/api/event/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_event.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.event_routes.create_flask_token")
    @patch("src.routes.event_routes.create_flask_breadcrumb")
    @patch("src.routes.event_routes.EventService.get_event")
    def test_get_event_not_found(
        self,
        mock_get_event,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/event/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_event.side_effect = HTTPNotFound(
            "Event 999 not found"
        )

        response = self.client.get("/api/event/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Event 999 not found")

    @patch("src.routes.event_routes.create_flask_token")
    def test_create_event_unauthorized(self, mock_create_token):
        """Test POST /api/event when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/event",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
