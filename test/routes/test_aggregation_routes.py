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

    @patch("src.routes.aggregation_routes.create_flask_token")
    @patch("src.routes.aggregation_routes.create_flask_breadcrumb")
    @patch("src.routes.aggregation_routes.AggregationService.get_aggregation_detail")
    def test_get_aggregation_detail_success(
        self,
        mock_get_detail,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_detail.return_value = {
            "aggregation": {
                "_id": self.resource_id,
                "resource_id": self.resource_id,
                "hits": 1,
            },
            "notes": [],
        }

        response = self.client.get(f"/api/aggregation/{self.resource_id}")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn("aggregation", data)
        self.assertIn("notes", data)
        self.assertIsInstance(data["notes"], list)
        mock_get_detail.assert_called_once_with(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.aggregation_routes.create_flask_token")
    def test_get_aggregation_detail_unauthorized(self, mock_create_token):
        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.get(f"/api/aggregation/{self.resource_id}")

        self.assertEqual(response.status_code, 401)

    @patch("src.routes.aggregation_routes.create_flask_token")
    @patch("src.routes.aggregation_routes.create_flask_breadcrumb")
    @patch("src.routes.aggregation_routes.AggregationService.get_aggregation_detail")
    def test_get_aggregation_detail_bad_request(
        self,
        mock_get_detail,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_detail.side_effect = HTTPBadRequest("Invalid resource_id format")

        response = self.client.get("/api/aggregation/invalid-id")

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
