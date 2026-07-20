"""
Unit tests for Resource routes.

These tests validate the Flask route layer for the Resource domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""

import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.resource_routes import create_resource_routes


class TestResourceRoutes(unittest.TestCase):
    """Test cases for Resource routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_resource_routes(),
            url_prefix="/api/resource",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.create_resource")
    @patch("src.routes.resource_routes.ResourceService.get_resource")
    def test_create_resource_success(
        self,
        mock_get_resource,
        mock_create_resource,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/resource for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_resource.return_value = "123"
        mock_get_resource.return_value = {
            "_id": "123",
            "name": "test-resource",
            "status": "active",
        }

        response = self.client.post(
            "/api/resource",
            json={"name": "test-resource", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_resource.assert_called_once()
        mock_get_resource.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resources")
    def test_get_resources_default_pagination(
        self,
        mock_get_resources,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """GET /api/resource returns a plain array with pagination headers."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_resources.return_value = [
            {"_id": "123", "name": "resource1"},
            {"_id": "456", "name": "resource2"},
        ]

        response = self.client.get("/api/resource")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(response.headers["X-Pagination-Offset"], "0")
        self.assertEqual(response.headers["X-Pagination-Size"], "20")
        self.assertEqual(response.headers["X-Pagination-Returned"], "2")
        mock_get_resources.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            offset=0,
            size=20,
            filters={},
            sort_by=[("name", 1), ("_id", 1)],
        )

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resources")
    def test_get_resources_with_headers_filter_and_order(
        self,
        mock_get_resources,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """GET /api/resource honors offset/size headers, filter + order params."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_resources.return_value = [{"_id": "123", "name": "test-resource"}]

        response = self.client.get(
            "/api/resource?name=test&sort_by=name&order=desc",
            headers={"offset": "5", "size": "10"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(response.headers["X-Pagination-Offset"], "5")
        self.assertEqual(response.headers["X-Pagination-Size"], "10")
        mock_get_resources.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            offset=5,
            size=10,
            filters={"name": "test"},
            sort_by=[("name", -1), ("_id", -1)],
        )

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resource")
    def test_get_resource_success(
        self,
        mock_get_resource,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/resource/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_resource.return_value = {
            "_id": "123",
            "name": "resource1",
        }

        response = self.client.get("/api/resource/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_resource.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resource")
    def test_get_resource_not_found(
        self,
        mock_get_resource,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/resource/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_resource.side_effect = HTTPNotFound("Resource 999 not found")

        response = self.client.get("/api/resource/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Resource 999 not found")

    @patch("src.routes.resource_routes.create_flask_token")
    def test_create_resource_unauthorized(self, mock_create_token):
        """Test POST /api/resource when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/resource",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
