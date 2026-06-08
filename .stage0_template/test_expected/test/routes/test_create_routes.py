"""
Unit tests for Create routes (create-style with POST and GET).
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.create_routes import create_create_routes


class TestCreateRoutes(unittest.TestCase):
    """Test cases for Create routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_create_routes(),
            url_prefix="/api/create",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.create_routes.create_flask_token")
    @patch("src.routes.create_routes.create_flask_breadcrumb")
    @patch("src.routes.create_routes.CreateService.create_create")
    @patch("src.routes.create_routes.CreateService.get_create")
    def test_create_create_success(
        self,
        mock_get_create,
        mock_create_create,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/create for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_create.return_value = "123"
        mock_get_create.return_value = {
            "_id": "123",
            "name": "test-create",
            "status": "active",
        }

        response = self.client.post(
            "/api/create",
            json={"name": "test-create", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_create.assert_called_once()
        mock_get_create.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.create_routes.create_flask_token")
    @patch("src.routes.create_routes.create_flask_breadcrumb")
    @patch("src.routes.create_routes.CreateService.get_creates")
    def test_get_creates_success(
        self,
        mock_get_creates,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/create for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_creates.return_value = {
            "items": [
                {"_id": "123", "name": "create1"},
                {"_id": "456", "name": "create2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/create")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_creates.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.create_routes.create_flask_token")
    @patch("src.routes.create_routes.create_flask_breadcrumb")
    @patch("src.routes.create_routes.CreateService.get_create")
    def test_get_create_success(
        self,
        mock_get_create,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/create/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_create.return_value = {
            "_id": "123",
            "name": "create1",
        }

        response = self.client.get("/api/create/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_create.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.create_routes.create_flask_token")
    @patch("src.routes.create_routes.create_flask_breadcrumb")
    @patch("src.routes.create_routes.CreateService.get_create")
    def test_get_create_not_found(
        self,
        mock_get_create,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/create/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_create.side_effect = HTTPNotFound(
            "Create 999 not found"
        )

        response = self.client.get("/api/create/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Create 999 not found")

    @patch("src.routes.create_routes.create_flask_token")
    def test_create_create_unauthorized(self, mock_create_token):
        """Test POST /api/create when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/create",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
