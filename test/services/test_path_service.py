"""
Unit tests for Path service.
"""

import unittest
from unittest.mock import patch, MagicMock
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
        self.mock_admin_token = {"user_id": "admin_user", "roles": ["admin"]}
        self.mock_mentor_token = {"user_id": "mentor_user", "roles": ["mentor"]}
        self.mock_user_token = {"user_id": "regular_user", "roles": ["user"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    def test_inherited_methods_exist(self):
        """Assert inherited GET methods exist on the subclass."""
        self.assertTrue(callable(getattr(PathService, "get_paths", None)))
        self.assertTrue(callable(getattr(PathService, "get_path", None)))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_create_path_allowed_for_mentor(self, mock_get_mongo, mock_get_config):
        """Test mentor may create a path."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "test-path", "status": "active"}
        path_id = PathService.create_path(
            data, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertEqual(path_id, "123")
        mock_mongo.create_document.assert_called_once()

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_create_path_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """Test admin may create a path."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "test-path", "status": "active"}
        path_id = PathService.create_path(
            data, self.mock_admin_token, self.mock_breadcrumb
        )

        self.assertEqual(path_id, "123")

    @patch("src.services.path_service.Config.get_instance")
    def test_create_path_forbidden_without_mentor_or_admin(self, mock_get_config):
        """Test create raises HTTPForbidden without mentor/admin."""
        mock_config = MagicMock()
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        data = {"name": "test-path"}
        with self.assertRaises(HTTPForbidden):
            PathService.create_path(data, self.mock_user_token, self.mock_breadcrumb)

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_create_path_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "name": "test"}
        PathService.create_path(data, self.mock_mentor_token, self.mock_breadcrumb)

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_create_path_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test create_path raises HTTPInternalServerError on exception."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("DB error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.create_path(
                {"name": "test"}, self.mock_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_allowed_for_mentor(self, mock_get_mongo, mock_get_config):
        """Test mentor may update a path."""
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

        data = {"name": "updated-path"}
        updated = PathService.update_path(
            "123", data, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "updated-path")

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """Test admin may update a path."""
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

        data = {"name": "updated-path"}
        updated = PathService.update_path(
            "123", data, self.mock_admin_token, self.mock_breadcrumb
        )

        self.assertEqual(updated["name"], "updated-path")

    @patch("src.services.path_service.Config.get_instance")
    def test_update_path_forbidden_without_mentor_or_admin(self, mock_get_config):
        """Test update raises HTTPForbidden without mentor/admin."""
        mock_config = MagicMock()
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        with self.assertRaises(HTTPForbidden):
            PathService.update_path(
                "123", {"name": "Updated"}, self.mock_user_token, self.mock_breadcrumb
            )

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

        data = {"_id": "999", "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PathService.update_path(
                "123", data, self.mock_mentor_token, self.mock_breadcrumb
            )
        self.assertIn("_id", str(context.exception))

        data = {"created": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PathService.update_path(
                "123", data, self.mock_mentor_token, self.mock_breadcrumb
            )
        self.assertIn("created", str(context.exception))

        data = {"saved": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PathService.update_path(
                "123", data, self.mock_mentor_token, self.mock_breadcrumb
            )
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
                "999",
                {"name": "Updated"},
                self.mock_mentor_token,
                self.mock_breadcrumb,
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_update_path_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test update_path raises HTTPInternalServerError on exception."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("DB error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.update_path(
                "123",
                {"name": "Updated"},
                self.mock_mentor_token,
                self.mock_breadcrumb,
            )


if __name__ == "__main__":
    unittest.main()
