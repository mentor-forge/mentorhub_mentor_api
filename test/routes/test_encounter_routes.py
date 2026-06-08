"""
Unit tests for Encounter routes.

These tests validate the Flask route layer for the Encounter domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.encounter_routes import create_encounter_routes


class TestEncounterRoutes(unittest.TestCase):
    """Test cases for Encounter routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_encounter_routes(),
            url_prefix="/api/encounter",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.routes.encounter_routes.EncounterService.create_encounter")
    @patch("src.routes.encounter_routes.EncounterService.get_encounter")
    def test_create_encounter_success(
        self,
        mock_get_encounter,
        mock_create_encounter,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/encounter for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_encounter.return_value = "123"
        mock_get_encounter.return_value = {
            "_id": "123",
            "name": "test-encounter",
            "status": "active",
        }

        response = self.client.post(
            "/api/encounter",
            json={"name": "test-encounter", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_encounter.assert_called_once()
        mock_get_encounter.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.routes.encounter_routes.EncounterService.get_encounters")
    def test_get_encounters_no_filter(
        self,
        mock_get_encounters,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/encounter without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_encounters.return_value = {
            "items": [
                {"_id": "123", "name": "encounter1"},
                {"_id": "456", "name": "encounter2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/encounter")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_encounters.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.routes.encounter_routes.EncounterService.get_encounters")
    def test_get_encounters_with_name_filter(
        self,
        mock_get_encounters,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/encounter with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_encounters.return_value = {
            "items": [{"_id": "123", "name": "test-encounter"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/encounter?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_encounters.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.routes.encounter_routes.EncounterService.get_encounter")
    def test_get_encounter_success(
        self,
        mock_get_encounter,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/encounter/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_encounter.return_value = {
            "_id": "123",
            "name": "encounter1",
        }

        response = self.client.get("/api/encounter/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_encounter.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.routes.encounter_routes.EncounterService.get_encounter")
    def test_get_encounter_not_found(
        self,
        mock_get_encounter,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/encounter/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_encounter.side_effect = HTTPNotFound(
            "Encounter 999 not found"
        )

        response = self.client.get("/api/encounter/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Encounter 999 not found")

    @patch("src.routes.encounter_routes.create_flask_token")
    def test_create_encounter_unauthorized(self, mock_create_token):
        """Test POST /api/encounter when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/encounter",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
