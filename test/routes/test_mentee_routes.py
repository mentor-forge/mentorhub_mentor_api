"""
Unit tests for Mentee routes.

These tests validate the Flask route layer for the Mentee domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""

import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.mentee_routes import create_mentee_routes

PROFILE_ID = "507f1f77bcf86cd799439011"
MENTEE_ID = "507f1f77bcf86cd7994390aa"


class TestMenteeRoutes(unittest.TestCase):
    """Test cases for Mentee routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_mentee_routes(),
            url_prefix="/api/mentee",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "mike", "roles": ["mentor"]}
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }

    @patch("src.routes.mentee_routes.create_flask_token")
    @patch("src.routes.mentee_routes.create_flask_breadcrumb")
    @patch("src.routes.mentee_routes.MenteeService.get_mentee")
    def test_get_mentee_success(
        self,
        mock_get_mentee,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/mentee/<profile_id> for a successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_mentee.return_value = {
            "_id": MENTEE_ID,
            "profile_id": PROFILE_ID,
            "status": "active",
        }

        response = self.client.get(f"/api/mentee/{PROFILE_ID}")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], MENTEE_ID)
        mock_get_mentee.assert_called_once_with(
            PROFILE_ID, self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.mentee_routes.create_flask_token")
    @patch("src.routes.mentee_routes.create_flask_breadcrumb")
    @patch("src.routes.mentee_routes.MenteeService.update_mentee")
    def test_update_mentee_success(
        self,
        mock_update_mentee,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test PATCH /api/mentee/<mentee_id> for a successful update."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_update_mentee.return_value = {
            "_id": MENTEE_ID,
            "focus": "async patterns",
        }

        response = self.client.patch(
            f"/api/mentee/{MENTEE_ID}",
            json={"focus": "async patterns"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["focus"], "async patterns")
        mock_update_mentee.assert_called_once_with(
            MENTEE_ID,
            {"focus": "async patterns"},
            self.mock_token,
            self.mock_breadcrumb,
        )

    @patch("src.routes.mentee_routes.create_flask_token")
    @patch("src.routes.mentee_routes.create_flask_breadcrumb")
    @patch("src.routes.mentee_routes.MenteeService.get_mentee")
    def test_get_mentee_forbidden(
        self,
        mock_get_mentee,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/mentee/<profile_id> when caller lacks the mentor role."""
        from api_utils.flask_utils.exceptions import HTTPForbidden

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_mentee.side_effect = HTTPForbidden(
            "Mentor role required to access mentee data"
        )

        response = self.client.get(f"/api/mentee/{PROFILE_ID}")

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json)

    @patch("src.routes.mentee_routes.create_flask_token")
    @patch("src.routes.mentee_routes.create_flask_breadcrumb")
    @patch("src.routes.mentee_routes.MenteeService.update_mentee")
    def test_update_mentee_not_found(
        self,
        mock_update_mentee,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test PATCH /api/mentee/<mentee_id> when the document is missing."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_update_mentee.side_effect = HTTPNotFound(f"Mentee {MENTEE_ID} not found")

        response = self.client.patch(
            f"/api/mentee/{MENTEE_ID}",
            json={"focus": "async patterns"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json)

    @patch("src.routes.mentee_routes.create_flask_token")
    def test_get_mentee_unauthorized(self, mock_create_token):
        """Test GET /api/mentee/<profile_id> when the token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.get(f"/api/mentee/{PROFILE_ID}")

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)

    @patch("src.routes.mentee_routes.create_flask_token")
    def test_update_mentee_unauthorized(self, mock_create_token):
        """Test PATCH /api/mentee/<mentee_id> when the token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.patch(
            f"/api/mentee/{MENTEE_ID}",
            json={"focus": "async patterns"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
