"""
Unit tests for {{item}} routes.

These tests validate the Flask route layer for the {{item}} domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.{{item | lower}}_routes import create_{{item | lower}}_routes


class Test{{item}}Routes(unittest.TestCase):
    """Test cases for {{item}} routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_{{item | lower}}_routes(),
            url_prefix="/api/{{item | lower}}",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.{{item | lower}}_routes.create_flask_token")
    @patch("src.routes.{{item | lower}}_routes.create_flask_breadcrumb")
    @patch("src.routes.{{item | lower}}_routes.{{item}}Service.create_{{item | lower}}")
    @patch("src.routes.{{item | lower}}_routes.{{item}}Service.get_{{item | lower}}")
    def test_create_{{item | lower}}_success(
        self,
        mock_get_{{item | lower}},
        mock_create_{{item | lower}},
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/{{item | lower}} for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_{{item | lower}}.return_value = "123"
        mock_get_{{item | lower}}.return_value = {
            "_id": "123",
            "name": "test-{{item | lower}}",
            "status": "active",
        }

        response = self.client.post(
            "/api/{{item | lower}}",
            json={"name": "test-{{item | lower}}", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_{{item | lower}}.assert_called_once()
        mock_get_{{item | lower}}.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.{{item | lower}}_routes.create_flask_token")
    @patch("src.routes.{{item | lower}}_routes.create_flask_breadcrumb")
    @patch("src.routes.{{item | lower}}_routes.{{item}}Service.get_{{item | lower}}s")
    def test_get_{{item | lower}}s_no_filter(
        self,
        mock_get_{{item | lower}}s,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/{{item | lower}} without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_{{item | lower}}s.return_value = {
            "items": [
                {"_id": "123", "name": "{{item | lower}}1"},
                {"_id": "456", "name": "{{item | lower}}2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/{{item | lower}}")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_{{item | lower}}s.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.{{item | lower}}_routes.create_flask_token")
    @patch("src.routes.{{item | lower}}_routes.create_flask_breadcrumb")
    @patch("src.routes.{{item | lower}}_routes.{{item}}Service.get_{{item | lower}}s")
    def test_get_{{item | lower}}s_with_name_filter(
        self,
        mock_get_{{item | lower}}s,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/{{item | lower}} with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_{{item | lower}}s.return_value = {
            "items": [{"_id": "123", "name": "test-{{item | lower}}"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/{{item | lower}}?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_{{item | lower}}s.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.{{item | lower}}_routes.create_flask_token")
    @patch("src.routes.{{item | lower}}_routes.create_flask_breadcrumb")
    @patch("src.routes.{{item | lower}}_routes.{{item}}Service.get_{{item | lower}}")
    def test_get_{{item | lower}}_success(
        self,
        mock_get_{{item | lower}},
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/{{item | lower}}/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_{{item | lower}}.return_value = {
            "_id": "123",
            "name": "{{item | lower}}1",
        }

        response = self.client.get("/api/{{item | lower}}/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_{{item | lower}}.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.{{item | lower}}_routes.create_flask_token")
    @patch("src.routes.{{item | lower}}_routes.create_flask_breadcrumb")
    @patch("src.routes.{{item | lower}}_routes.{{item}}Service.get_{{item | lower}}")
    def test_get_{{item | lower}}_not_found(
        self,
        mock_get_{{item | lower}},
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/{{item | lower}}/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_{{item | lower}}.side_effect = HTTPNotFound(
            "{{item}} 999 not found"
        )

        response = self.client.get("/api/{{item | lower}}/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "{{item}} 999 not found")

    @patch("src.routes.{{item | lower}}_routes.create_flask_token")
    def test_create_{{item | lower}}_unauthorized(self, mock_create_token):
        """Test POST /api/{{item | lower}} when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/{{item | lower}}",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()

