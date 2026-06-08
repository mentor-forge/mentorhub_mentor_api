"""
Unit tests for Path routes.

These tests validate the Flask route layer for the Path domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.path_routes import create_path_routes


class TestPathRoutes(unittest.TestCase):
    """Test cases for Path routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_path_routes(),
            url_prefix="/api/path",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.create_path")
    @patch("src.routes.path_routes.PathService.get_path")
    def test_create_path_success(
        self,
        mock_get_path,
        mock_create_path,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/path for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_path.return_value = "123"
        mock_get_path.return_value = {
            "_id": "123",
            "name": "test-path",
            "status": "active",
        }

        response = self.client.post(
            "/api/path",
            json={"name": "test-path", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_path.assert_called_once()
        mock_get_path.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_paths")
    def test_get_paths_no_filter(
        self,
        mock_get_paths,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_paths.return_value = {
            "items": [
                {"_id": "123", "name": "path1"},
                {"_id": "456", "name": "path2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/path")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_paths.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_paths")
    def test_get_paths_with_name_filter(
        self,
        mock_get_paths,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_paths.return_value = {
            "items": [{"_id": "123", "name": "test-path"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/path?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_paths.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_path")
    def test_get_path_success(
        self,
        mock_get_path,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_path.return_value = {
            "_id": "123",
            "name": "path1",
        }

        response = self.client.get("/api/path/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_path.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_path")
    def test_get_path_not_found(
        self,
        mock_get_path,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_path.side_effect = HTTPNotFound(
            "Path 999 not found"
        )

        response = self.client.get("/api/path/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Path 999 not found")

    @patch("src.routes.path_routes.create_flask_token")
    def test_create_path_unauthorized(self, mock_create_token):
        """Test POST /api/path when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/path",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
