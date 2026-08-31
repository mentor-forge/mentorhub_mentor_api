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
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.services.encounter_service.EncounterService.create_encounter")
    @patch("src.services.encounter_service.EncounterService.get_encounter")
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
            json={
                "name": "test-encounter",
                "status": "active",
                "mentor_id": "507f1f77bcf86cd799439011",
                "mentee_id": "507f1f77bcf86cd799439012",
                "plan_id": "507f1f77bcf86cd799439013",
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_encounter.assert_called_once()
        mock_get_encounter.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.encounter_service.EncounterService.get_encounters_for_mentee")
    def test_get_encounters_success(
        self,
        mock_get_encounters,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """GET /api/encounter?mentee_id=... returns a list of encounters."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_encounters.return_value = [
            {"_id": "123", "name": "encounter 1"},
            {"_id": "456", "name": "encounter 2"},
        ]

        response = self.client.get("/api/encounter?mentee_id=507f1f77bcf86cd799439012")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        mock_get_encounters.assert_called_once_with(
            "507f1f77bcf86cd799439012",
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
        )

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    def test_get_encounters_missing_mentee_id(
        self,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """GET /api/encounter returns 400 when mentee_id is missing."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        response = self.client.get("/api/encounter")

        self.assertEqual(response.status_code, 400)
        self.assertIn("mentee_id", response.json["error"])

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.encounter_service.EncounterService.get_encounter")
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

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.encounter_service.EncounterService.get_encounter")
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

        mock_get_encounter.side_effect = HTTPNotFound("Encounter 999 not found")

        response = self.client.get("/api/encounter/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Encounter 999 not found")

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.services.encounter_service.EncounterService.update_encounter")
    def test_update_encounter_success(
        self,
        mock_update_encounter,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """PATCH /api/encounter/<id> returns 200 with the updated document."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_update_encounter.return_value = {
            "_id": "123",
            "name": "updated-encounter",
        }

        response = self.client.patch(
            "/api/encounter/123",
            json={"name": "updated-encounter"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "updated-encounter")
        mock_update_encounter.assert_called_once_with(
            "123",
            {"name": "updated-encounter"},
            self.mock_token,
            self.mock_breadcrumb,
        )

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.services.encounter_service.EncounterService.update_encounter")
    def test_update_encounter_forbidden(
        self,
        mock_update_encounter,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """PATCH /api/encounter/<id> returns 403 for a non-owner / wrong role."""
        from api_utils.flask_utils.exceptions import HTTPForbidden

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_update_encounter.side_effect = HTTPForbidden(
            "Only the owning mentor or an admin may update this encounter"
        )

        response = self.client.patch(
            "/api/encounter/123",
            json={"name": "updated-encounter"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json)

    @patch("src.routes.encounter_routes.create_flask_token")
    @patch("src.routes.encounter_routes.create_flask_breadcrumb")
    @patch("src.services.encounter_service.EncounterService.update_encounter")
    def test_update_encounter_not_found(
        self,
        mock_update_encounter,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """PATCH /api/encounter/<id> returns 404 when the encounter is missing."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_update_encounter.side_effect = HTTPNotFound("Encounter 999 not found")

        response = self.client.patch(
            "/api/encounter/999",
            json={"name": "updated-encounter"},
        )

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
