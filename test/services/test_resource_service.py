"""
Unit tests for Resource service.
"""
import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.resource_service import ResourceService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestResourceService(unittest.TestCase):
    """Test cases for ResourceService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_create_resource_success(self, mock_get_mongo, mock_get_config):
        """Test successful creation of a resource document."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {
            "name": "test-resource",
            "description": "Test resource",
            "status": "active",
        }

        resource_id = ResourceService.create_resource(
            data, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(resource_id, "123")
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Resource")
        created_data = call_args[0][1]
        self.assertIn("created", created_data)
        self.assertIn("saved", created_data)
        self.assertEqual(created_data["name"], "test-resource")

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_create_resource_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "name": "test"}

        ResourceService.create_resource(
            data, self.mock_token, self.mock_breadcrumb
        )

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_first_batch(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of first batch (no cursor)."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter(
            [
                {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "resource1"},
                {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "resource2"},
            ]
        )

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        result = ResourceService.get_resources(
            self.mock_token, self.mock_breadcrumb, limit=10
        )

        self.assertIn("items", result)
        self.assertIn("limit", result)
        self.assertIn("has_more", result)
        self.assertIn("next_cursor", result)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["limit"], 10)
        self.assertFalse(result["has_more"])
        self.assertIsNone(result["next_cursor"])

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_invalid_limit_too_small(self, mock_get_mongo, mock_get_config):
        """Test get_resources raises HTTPBadRequest for limit < 1."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            ResourceService.get_resources(
                self.mock_token, self.mock_breadcrumb, limit=0
            )
        self.assertIn("limit must be >= 1", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_invalid_limit_too_large(self, mock_get_mongo, mock_get_config):
        """Test get_resources raises HTTPBadRequest for limit > 100."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            ResourceService.get_resources(
                self.mock_token, self.mock_breadcrumb, limit=101
            )
        self.assertIn("limit must be <= 100", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_invalid_sort_by(self, mock_get_mongo, mock_get_config):
        """Test get_resources raises HTTPBadRequest for invalid sort_by."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            ResourceService.get_resources(
                self.mock_token,
                self.mock_breadcrumb,
                sort_by="invalid_field",
            )
        self.assertIn("sort_by must be one of", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_invalid_order(self, mock_get_mongo, mock_get_config):
        """Test get_resources raises HTTPBadRequest for invalid order."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            ResourceService.get_resources(
                self.mock_token,
                self.mock_breadcrumb,
                order="invalid",
            )
        self.assertIn("order must be 'asc' or 'desc'", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_invalid_after_id(self, mock_get_mongo, mock_get_config):
        """Test get_resources raises HTTPBadRequest for invalid after_id."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            ResourceService.get_resources(
                self.mock_token,
                self.mock_breadcrumb,
                after_id="invalid",
            )
        self.assertIn("after_id must be a valid MongoDB ObjectId", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resource_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific resource document."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "resource1",
        }
        mock_get_mongo.return_value = mock_mongo

        result = ResourceService.get_resource(
            "123", self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Resource", "123")

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resource_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_resource raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            ResourceService.get_resource(
                "999", self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_success(self, mock_get_mongo, mock_get_config):
        """Test successful update of a resource document."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": "123",
            "name": "updated-resource",
        }
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "updated-resource", "description": "Updated"}

        updated = ResourceService.update_resource(
            "123", data, self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "updated-resource")
        mock_mongo.update_document.assert_called_once()
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[1]["document_id"], "123")
        set_data = call_args[1]["set_data"]
        self.assertIn("saved", set_data)
        self.assertEqual(set_data["name"], "updated-resource")

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_resource raises HTTPForbidden for restricted fields."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "999", "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ResourceService.update_resource(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("_id", str(context.exception))

        data = {"created": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ResourceService.update_resource(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("created", str(context.exception))

        data = {"saved": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ResourceService.update_resource(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("saved", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_not_found(self, mock_get_mongo, mock_get_config):
        """Test update_resource raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            ResourceService.update_resource(
                "999", {"name": "Updated"}, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_uses_breadcrumb_directly(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_resource uses breadcrumb directly for saved field."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {"_id": "123", "name": "updated"}
        mock_get_mongo.return_value = mock_mongo

        breadcrumb = {
            "from_ip": "192.168.1.1",
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "correlation_id": "test-id",
        }

        result = ResourceService.update_resource(
            "123", {"name": "updated"}, self.mock_token, breadcrumb
        )

        self.assertIsNotNone(result)
        call_args = mock_mongo.update_document.call_args
        set_data = call_args[1]["set_data"]
        self.assertEqual(set_data["saved"], breadcrumb)
        self.assertEqual(set_data["saved"]["from_ip"], "192.168.1.1")

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_create_resource_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test create_resource handles database exceptions."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            ResourceService.create_resource(
                {"name": "test"}, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test get_resources handles database exceptions."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_collection.find.side_effect = Exception("Database error")

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            ResourceService.get_resources(
                self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resource_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test get_resource handles database exceptions."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            ResourceService.get_resource(
                "123", self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_resource handles database exceptions."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            ResourceService.update_resource(
                "123", {"name": "updated"}, self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
