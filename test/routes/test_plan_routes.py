"""
Unit tests for Plan routes.

These tests validate the Flask route layer for the Plan domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.plan_routes import create_plan_routes


class TestPlanRoutes(unittest.TestCase):
    """Test cases for Plan routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_plan_routes(),
            url_prefix="/api/plan",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.plan_routes.create_flask_token")
    @patch("src.routes.plan_routes.create_flask_breadcrumb")
    @patch("src.routes.plan_routes.PlanService.create_plan")
    @patch("src.routes.plan_routes.PlanService.get_plan")
    def test_create_plan_success(
        self,
        mock_get_plan,
        mock_create_plan,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/plan for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_plan.return_value = "123"
        mock_get_plan.return_value = {
            "_id": "123",
            "name": "test-plan",
            "status": "active",
        }

        response = self.client.post(
            "/api/plan",
            json={"name": "test-plan", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_plan.assert_called_once()
        mock_get_plan.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.plan_routes.create_flask_token")
    @patch("src.routes.plan_routes.create_flask_breadcrumb")
    @patch("src.routes.plan_routes.PlanService.get_plans")
    def test_get_plans_no_filter(
        self,
        mock_get_plans,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/plan without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_plans.return_value = {
            "items": [
                {"_id": "123", "name": "plan1"},
                {"_id": "456", "name": "plan2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/plan")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_plans.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.plan_routes.create_flask_token")
    @patch("src.routes.plan_routes.create_flask_breadcrumb")
    @patch("src.routes.plan_routes.PlanService.get_plans")
    def test_get_plans_with_name_filter(
        self,
        mock_get_plans,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/plan with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_plans.return_value = {
            "items": [{"_id": "123", "name": "test-plan"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/plan?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_plans.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.plan_routes.create_flask_token")
    @patch("src.routes.plan_routes.create_flask_breadcrumb")
    @patch("src.routes.plan_routes.PlanService.get_plan")
    def test_get_plan_success(
        self,
        mock_get_plan,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/plan/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_plan.return_value = {
            "_id": "123",
            "name": "plan1",
        }

        response = self.client.get("/api/plan/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_plan.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.plan_routes.create_flask_token")
    @patch("src.routes.plan_routes.create_flask_breadcrumb")
    @patch("src.routes.plan_routes.PlanService.get_plan")
    def test_get_plan_not_found(
        self,
        mock_get_plan,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/plan/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_plan.side_effect = HTTPNotFound(
            "Plan 999 not found"
        )

        response = self.client.get("/api/plan/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Plan 999 not found")

    @patch("src.routes.plan_routes.create_flask_token")
    def test_create_plan_unauthorized(self, mock_create_token):
        """Test POST /api/plan when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/plan",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
