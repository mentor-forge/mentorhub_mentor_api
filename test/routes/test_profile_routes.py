"""
Unit tests for Profile routes (consume-style, read-only).
"""

import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.profile_routes import create_profile_routes


class TestProfileRoutes(unittest.TestCase):
    """Test cases for Profile routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_profile_routes(),
            url_prefix="/api/profile",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.profile_service.ProfileService.get_profiles")
    def test_get_profiles_success(
        self,
        mock_get_profiles,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/profile returns the Mentor Dashboard array."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_profiles.return_value = [
            {
                "_id": "123",
                "name": "daniel",
                "description": "mentee one",
                "progress": {"library": 3, "now": 1, "next": 2},
                "last_encounter": None,
            },
            {
                "_id": "456",
                "name": "lucky",
                "description": "mentee two",
                "progress": {"library": 0, "now": 0, "next": 0},
                "last_encounter": None,
            },
        ]

        response = self.client.get("/api/profile")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["progress"], {"library": 3, "now": 1, "next": 2})
        mock_get_profiles.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
            {},
            [("display_name", 1), ("_id", 1)],
        )

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.profile_service.ProfileService.get_profiles")
    def test_get_profiles_with_query_params(
        self,
        mock_get_profiles,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Query parameters are parsed per filter/order spec and passed to service."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_profiles.return_value = []

        response = self.client.get("/api/profile?display_name=test")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])
        mock_get_profiles.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
            {"display_name": "test"},
            [("display_name", 1), ("_id", 1)],
        )

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.profile_service.ProfileService.get_profile")
    def test_get_profile_success(
        self,
        mock_get_profile,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/profile/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_profile.return_value = {
            "_id": "123",
            "name": "profile1",
        }

        response = self.client.get("/api/profile/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_profile.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.profile_service.ProfileService.get_profile")
    def test_get_profile_not_found(
        self,
        mock_get_profile,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/profile/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_profile.side_effect = HTTPNotFound("Profile 999 not found")

        response = self.client.get("/api/profile/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Profile 999 not found")

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    def test_get_profiles_unauthorized(self, mock_create_token):
        """Test GET /api/profile when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.get("/api/profile")

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.profile_service.ProfileService.get_profiles")
    def test_get_profiles_forbidden(
        self,
        mock_get_profiles,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """A service HTTPForbidden is translated to a 403 by the route wrapper."""
        from api_utils.flask_utils.exceptions import HTTPForbidden

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_profiles.side_effect = HTTPForbidden(
            "Mentor role required to access profile data"
        )

        response = self.client.get("/api/profile")

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json)

    @patch("src.routes.profile_routes.create_flask_token")
    @patch("src.routes.profile_routes.create_flask_breadcrumb")
    @patch("src.services.profile_service.ProfileService.get_profile_properties")
    def test_get_profile_properties_success(
        self,
        mock_get_profile_properties,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/profile/<id>/properties for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_profile_properties.return_value = {
            "profile": {"_id": "123", "name": "daniel"},
            "status_summary": {
                "library_count": 1,
                "now_count": 0,
                "next_count": 0,
                "encounters_count": 0,
                "resources_engaged": 1,
            },
            "sites_and_links": [],
            "mentor_history": [],
            "journey": None,
            "path": None,
            "resource_usage": [],
            "celebrations": [],
        }

        response = self.client.get("/api/profile/123/properties")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["profile"]["name"], "daniel")
        mock_get_profile_properties.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )


if __name__ == "__main__":
    unittest.main()
