"""
Unit tests for Path service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.path_service import PathService
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestPathService(unittest.TestCase):
    """Test cases for PathService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_create_path_success(self, mock_get_mongo, mock_get_config):
        """Test successful creation of a path document."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {
            "name": "test-path",
            "description": "Test path",
            "status": "active",
        }

        path_id = PathService.create_path(data, self.mock_token, self.mock_breadcrumb)

        self.assertEqual(path_id, "123")
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Path")
        created_data = call_args[0][1]
        self.assertIn("created", created_data)
        self.assertIn("saved", created_data)
        self.assertEqual(created_data["name"], "test-path")

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_create_path_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "name": "test"}

        PathService.create_path(data, self.mock_token, self.mock_breadcrumb)

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.path_service.SharedPathService")
    def test_get_paths_delegates_to_shared(self, mock_shared):
        """The Path list read delegates to the shared PathService."""
        docs = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "path1"},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "path2"},
        ]
        mock_shared.get_paths.return_value = docs

        sort_by = [("name", 1), ("_id", 1)]
        result = PathService.get_paths(
            self.mock_token,
            self.mock_breadcrumb,
            offset=0,
            size=20,
            filters={"name": "test"},
            sort_by=sort_by,
        )

        self.assertEqual(result, docs)
        mock_shared.get_paths.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            offset=0,
            size=20,
            filters={"name": "test"},
            sort_by=sort_by,
        )

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific path document."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "path1",
        }
        mock_get_mongo.return_value = mock_mongo

        result = PathService.get_path("123", self.mock_token, self.mock_breadcrumb)

        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Path", "123")

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_path raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            PathService.get_path("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_success(self, mock_get_mongo, mock_get_config):
        """Test successful update of a path document."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": "123",
            "name": "updated-path",
        }
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "updated-path", "description": "Updated"}

        updated = PathService.update_path(
            "123", data, self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "updated-path")
        mock_mongo.update_document.assert_called_once()
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[1]["document_id"], "123")
        set_data = call_args[1]["set_data"]
        self.assertIn("saved", set_data)
        self.assertEqual(set_data["name"], "updated-path")

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_path raises HTTPForbidden for restricted fields."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "999", "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PathService.update_path("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("_id", str(context.exception))

        data = {"created": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PathService.update_path("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("created", str(context.exception))

        data = {"saved": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PathService.update_path("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("saved", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_not_found(self, mock_get_mongo, mock_get_config):
        """Test update_path raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            PathService.update_path(
                "999", {"name": "Updated"}, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_uses_breadcrumb_directly(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_path uses breadcrumb directly for saved field."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
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

        result = PathService.update_path(
            "123", {"name": "updated"}, self.mock_token, breadcrumb
        )

        self.assertIsNotNone(result)
        call_args = mock_mongo.update_document.call_args
        set_data = call_args[1]["set_data"]
        self.assertEqual(set_data["saved"], breadcrumb)
        self.assertEqual(set_data["saved"]["from_ip"], "192.168.1.1")

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_allowed_for_mentor(self, mock_get_mongo, mock_get_config):
        """Test update_path is allowed for a mentor (non-admin) caller."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {"_id": "123", "name": "updated"}
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "m", "roles": ["mentor"]}
        result = PathService.update_path(
            "123", {"name": "updated"}, token, self.mock_breadcrumb
        )

        self.assertEqual(result["name"], "updated")
        mock_mongo.update_document.assert_called_once()

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_denied_for_non_privileged(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_path denies a caller lacking mentor/admin (403)."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "u", "roles": ["mentee"]}
        with self.assertRaises(HTTPForbidden):
            PathService.update_path("123", {"name": "x"}, token, self.mock_breadcrumb)
        mock_mongo.update_document.assert_not_called()

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_denied_for_no_roles(self, mock_get_mongo, mock_get_config):
        """Test update_path denies a caller with no roles claim (403)."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "u"}
        with self.assertRaises(HTTPForbidden):
            PathService.update_path("123", {"name": "x"}, token, self.mock_breadcrumb)
        mock_mongo.update_document.assert_not_called()

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_create_path_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test create_path handles database exceptions."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.create_path(
                {"name": "test"}, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.path_service.SharedPathService")
    def test_get_paths_propagates_shared_errors(self, mock_shared):
        """Errors from the shared service surface unchanged."""
        mock_shared.get_paths.side_effect = HTTPInternalServerError(
            "Failed to retrieve paths"
        )
        with self.assertRaises(HTTPInternalServerError):
            PathService.get_paths(self.mock_token, self.mock_breadcrumb)

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_path handles database exceptions."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.get_path("123", self.mock_token, self.mock_breadcrumb)

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test update_path handles database exceptions."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.update_path(
                "123", {"name": "updated"}, self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
