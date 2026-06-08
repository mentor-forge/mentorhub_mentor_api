"""
Unit tests for Control routes.

These tests validate the Flask route layer for the Control domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.control_routes import create_control_routes


class TestControlRoutes(unittest.TestCase):
    """Test cases for Control routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_control_routes(),
            url_prefix="/api/control",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.control_routes.create_flask_token")
    @patch("src.routes.control_routes.create_flask_breadcrumb")
    @patch("src.routes.control_routes.ControlService.create_control")
    @patch("src.routes.control_routes.ControlService.get_control")
    def test_create_control_success(
        self,
        mock_get_control,
        mock_create_control,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/control for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_control.return_value = "123"
        mock_get_control.return_value = {
            "_id": "123",
            "name": "test-control",
            "status": "active",
        }

        response = self.client.post(
            "/api/control",
            json={"name": "test-control", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_control.assert_called_once()
        mock_get_control.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.control_routes.create_flask_token")
    @patch("src.routes.control_routes.create_flask_breadcrumb")
    @patch("src.routes.control_routes.ControlService.get_controls")
    def test_get_controls_no_filter(
        self,
        mock_get_controls,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/control without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_controls.return_value = {
            "items": [
                {"_id": "123", "name": "control1"},
                {"_id": "456", "name": "control2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/control")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_controls.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.control_routes.create_flask_token")
    @patch("src.routes.control_routes.create_flask_breadcrumb")
    @patch("src.routes.control_routes.ControlService.get_controls")
    def test_get_controls_with_name_filter(
        self,
        mock_get_controls,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/control with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_controls.return_value = {
            "items": [{"_id": "123", "name": "test-control"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/control?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_controls.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.control_routes.create_flask_token")
    @patch("src.routes.control_routes.create_flask_breadcrumb")
    @patch("src.routes.control_routes.ControlService.get_control")
    def test_get_control_success(
        self,
        mock_get_control,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/control/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_control.return_value = {
            "_id": "123",
            "name": "control1",
        }

        response = self.client.get("/api/control/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_control.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.control_routes.create_flask_token")
    @patch("src.routes.control_routes.create_flask_breadcrumb")
    @patch("src.routes.control_routes.ControlService.get_control")
    def test_get_control_not_found(
        self,
        mock_get_control,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/control/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_control.side_effect = HTTPNotFound(
            "Control 999 not found"
        )

        response = self.client.get("/api/control/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Control 999 not found")

    @patch("src.routes.control_routes.create_flask_token")
    def test_create_control_unauthorized(self, mock_create_token):
        """Test POST /api/control when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/control",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
