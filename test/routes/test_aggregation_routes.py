"""
Unit tests for Aggregation routes.
"""

import unittest
from unittest.mock import patch
from flask import Flask
from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPUnauthorized
from src.routes.aggregation_routes import create_aggregation_routes


class TestAggregationRoutes(unittest.TestCase):
    """Test cases for Aggregation routes."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_aggregation_routes(),
            url_prefix="/api/aggregation",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }
        self.resource_id = "507f1f77bcf86cd799439011"

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch(
        "src.services.aggregation_service.AggregationService.get_aggregation_for_resource"
    )
    def test_get_aggregation_success(
        self,
        mock_get_aggregation,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_aggregation.return_value = {
            "_id": self.resource_id,
            "resource_id": self.resource_id,
            "hits": 1,
        }

        response = self.client.get(f"/api/aggregation/{self.resource_id}")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], self.resource_id)
        self.assertEqual(data["hits"], 1)
        mock_get_aggregation.assert_called_once_with(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch(
        "src.services.aggregation_service.AggregationService.get_aggregation_for_resource"
    )
    def test_get_aggregation_null_when_unavailable(
        self,
        mock_get_aggregation,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_aggregation.return_value = None

        response = self.client.get(f"/api/aggregation/{self.resource_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json)

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch(
        "src.services.aggregation_service.AggregationService.get_aggregation_for_resource"
    )
    def test_get_aggregation_bad_request(
        self,
        mock_get_aggregation,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_aggregation.side_effect = HTTPBadRequest("Invalid resource_id")

        response = self.client.get("/api/aggregation/invalid-id")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    def test_get_aggregation_unauthorized(self, mock_create_token):
        mock_create_token.side_effect = HTTPUnauthorized("Unauthorized")

        response = self.client.get(f"/api/aggregation/{self.resource_id}")

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
