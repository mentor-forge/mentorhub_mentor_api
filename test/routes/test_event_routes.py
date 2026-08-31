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
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }

    @patch("src.routes.event_routes.create_flask_token")
    @patch("src.routes.event_routes.create_flask_breadcrumb")
    @patch("src.services.event_service.EventService.create_event")
    def test_create_event_success(
        self,
        mock_create_event,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/event for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_event.return_value = {
            "_id": "123",
            "type": "login",
            "context": {"profile_id": "000000000000000000000001"},
        }

        response = self.client.post(
            "/api/event",
            json={
                "type": "login",
                "context": {"profile_id": "000000000000000000000001"},
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_event.assert_called_once_with(
            {
                "type": "login",
                "context": {"profile_id": "000000000000000000000001"},
            },
            self.mock_token,
            self.mock_breadcrumb,
        )

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.event_service.EventService.get_events")
    def test_get_events_default_pagination(
        self,
        mock_get_events,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """GET /api/event returns a plain JSON array."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_events.return_value = [
            {"_id": "123", "type": "login"},
            {"_id": "456", "type": "logout"},
        ]

        response = self.client.get("/api/event")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        mock_get_events.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
            {},
            [("created.at_time", -1), ("_id", -1)],
        )

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.event_service.EventService.get_events")
    def test_get_events_with_filters_and_scope(
        self,
        mock_get_events,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """GET /api/event honors offset/size headers, type filter, profile scope."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_events.return_value = [{"_id": "123", "type": "login"}]

        response = self.client.get(
            "/api/event?type=login&sort_by=type&order=asc"
            "&profile_id=507f1f77bcf86cd799439099",
            headers={"offset": "0", "size": "5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        mock_get_events.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            5,
            {"type": ["login"]},
            [("type", 1), ("_id", 1)],
            profile_id="507f1f77bcf86cd799439099",
        )

    @patch("src.routes.event_routes.create_flask_token")
    @patch("src.routes.event_routes.create_flask_breadcrumb")
    @patch("src.services.event_service.EventService.get_event")
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
            "type": "login",
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
    @patch("src.services.event_service.EventService.get_event")
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

        mock_get_event.side_effect = HTTPNotFound("Event 999 not found")

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
            json={"type": "login"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
