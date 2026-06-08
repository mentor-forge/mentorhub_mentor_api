"""
Unit tests for {{item}} service.
"""
import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.{{item | lower}}_service import {{item}}Service
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class Test{{item}}Service(unittest.TestCase):
    """Test cases for {{item}}Service."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_create_{{item | lower}}_success(self, mock_get_mongo, mock_get_config):
        """Test successful creation of a {{item | lower}} document."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {
            "name": "test-{{item | lower}}",
            "description": "Test {{item | lower}}",
            "status": "active",
        }

        {{item | lower}}_id = {{item}}Service.create_{{item | lower}}(
            data, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual({{item | lower}}_id, "123")
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "{{item}}")
        created_data = call_args[0][1]
        self.assertIn("created", created_data)
        self.assertIn("saved", created_data)
        self.assertEqual(created_data["name"], "test-{{item | lower}}")

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_create_{{item | lower}}_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "name": "test"}

        {{item}}Service.create_{{item | lower}}(
            data, self.mock_token, self.mock_breadcrumb
        )

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}s_first_batch(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of first batch (no cursor)."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter(
            [
                {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "{{item | lower}}1"},
                {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "{{item | lower}}2"},
            ]
        )

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        result = {{item}}Service.get_{{item | lower}}s(
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

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}s_invalid_limit_too_small(self, mock_get_mongo, mock_get_config):
        """Test get_{{item | lower}}s raises HTTPBadRequest for limit < 1."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            {{item}}Service.get_{{item | lower}}s(
                self.mock_token, self.mock_breadcrumb, limit=0
            )
        self.assertIn("limit must be >= 1", str(context.exception))

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}s_invalid_limit_too_large(self, mock_get_mongo, mock_get_config):
        """Test get_{{item | lower}}s raises HTTPBadRequest for limit > 100."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            {{item}}Service.get_{{item | lower}}s(
                self.mock_token, self.mock_breadcrumb, limit=101
            )
        self.assertIn("limit must be <= 100", str(context.exception))

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}s_invalid_sort_by(self, mock_get_mongo, mock_get_config):
        """Test get_{{item | lower}}s raises HTTPBadRequest for invalid sort_by."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            {{item}}Service.get_{{item | lower}}s(
                self.mock_token,
                self.mock_breadcrumb,
                sort_by="invalid_field",
            )
        self.assertIn("sort_by must be one of", str(context.exception))

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}s_invalid_order(self, mock_get_mongo, mock_get_config):
        """Test get_{{item | lower}}s raises HTTPBadRequest for invalid order."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            {{item}}Service.get_{{item | lower}}s(
                self.mock_token,
                self.mock_breadcrumb,
                order="invalid",
            )
        self.assertIn("order must be 'asc' or 'desc'", str(context.exception))

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}s_invalid_after_id(self, mock_get_mongo, mock_get_config):
        """Test get_{{item | lower}}s raises HTTPBadRequest for invalid after_id."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            {{item}}Service.get_{{item | lower}}s(
                self.mock_token,
                self.mock_breadcrumb,
                after_id="invalid",
            )
        self.assertIn("after_id must be a valid MongoDB ObjectId", str(context.exception))

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific {{item | lower}} document."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "{{item | lower}}1",
        }
        mock_get_mongo.return_value = mock_mongo

        result = {{item}}Service.get_{{item | lower}}(
            "123", self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("{{item}}", "123")

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_{{item | lower}} raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            {{item}}Service.get_{{item | lower}}(
                "999", self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_update_{{item | lower}}_success(self, mock_get_mongo, mock_get_config):
        """Test successful update of a {{item | lower}} document."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": "123",
            "name": "updated-{{item | lower}}",
        }
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "updated-{{item | lower}}", "description": "Updated"}

        updated = {{item}}Service.update_{{item | lower}}(
            "123", data, self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "updated-{{item | lower}}")
        mock_mongo.update_document.assert_called_once()
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[1]["document_id"], "123")
        set_data = call_args[1]["set_data"]
        self.assertIn("saved", set_data)
        self.assertEqual(set_data["name"], "updated-{{item | lower}}")

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_update_{{item | lower}}_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_{{item | lower}} raises HTTPForbidden for restricted fields."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "999", "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            {{item}}Service.update_{{item | lower}}(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("_id", str(context.exception))

        data = {"created": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            {{item}}Service.update_{{item | lower}}(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("created", str(context.exception))

        data = {"saved": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            {{item}}Service.update_{{item | lower}}(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("saved", str(context.exception))

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_update_{{item | lower}}_not_found(self, mock_get_mongo, mock_get_config):
        """Test update_{{item | lower}} raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            {{item}}Service.update_{{item | lower}}(
                "999", {"name": "Updated"}, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_update_{{item | lower}}_uses_breadcrumb_directly(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_{{item | lower}} uses breadcrumb directly for saved field."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
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

        result = {{item}}Service.update_{{item | lower}}(
            "123", {"name": "updated"}, self.mock_token, breadcrumb
        )

        self.assertIsNotNone(result)
        call_args = mock_mongo.update_document.call_args
        set_data = call_args[1]["set_data"]
        self.assertEqual(set_data["saved"], breadcrumb)
        self.assertEqual(set_data["saved"]["from_ip"], "192.168.1.1")

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_create_{{item | lower}}_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test create_{{item | lower}} handles database exceptions."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            {{item}}Service.create_{{item | lower}}(
                {"name": "test"}, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}s_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test get_{{item | lower}}s handles database exceptions."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_collection.find.side_effect = Exception("Database error")

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            {{item}}Service.get_{{item | lower}}s(
                self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_get_{{item | lower}}_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test get_{{item | lower}} handles database exceptions."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            {{item}}Service.get_{{item | lower}}(
                "123", self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.{{item | lower}}_service.Config.get_instance")
    @patch("src.services.{{item | lower}}_service.MongoIO.get_instance")
    def test_update_{{item | lower}}_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_{{item | lower}} handles database exceptions."""
        mock_config = MagicMock()
        mock_config.{{ (item | upper) }}_COLLECTION_NAME = "{{item}}"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            {{item}}Service.update_{{item | lower}}(
                "123", {"name": "updated"}, self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()

