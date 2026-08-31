"""
Unit tests for Resource service.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.services.resource_service import ResourceService
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestResourceService(unittest.TestCase):
    """Test cases for ResourceService."""

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
        self.assertTrue(callable(getattr(ResourceService, "get_resources", None)))
        self.assertTrue(callable(getattr(ResourceService, "get_resource", None)))
        self.assertTrue(
            callable(getattr(ResourceService, "get_resources_by_ids", None))
        )

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_create_resource_allowed_for_mentor(self, mock_get_mongo, mock_get_config):
        """Test mentor may create a resource."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "test-resource", "status": "active"}
        resource_id = ResourceService.create_resource(
            data, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertEqual(resource_id, "123")
        mock_mongo.create_document.assert_called_once()

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_create_resource_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """Test admin may create a resource."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "test-resource", "status": "active"}
        resource_id = ResourceService.create_resource(
            data, self.mock_admin_token, self.mock_breadcrumb
        )

        self.assertEqual(resource_id, "123")

    @patch("src.services.resource_service.Config.get_instance")
    def test_create_resource_forbidden_without_mentor_or_admin(self, mock_get_config):
        """Test create raises HTTPForbidden without mentor/admin."""
        mock_config = MagicMock()
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        data = {"name": "test-resource"}
        with self.assertRaises(HTTPForbidden):
            ResourceService.create_resource(
                data, self.mock_user_token, self.mock_breadcrumb
            )

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_create_resource_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "name": "test"}
        ResourceService.create_resource(
            data, self.mock_mentor_token, self.mock_breadcrumb
        )

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_create_resource_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test create_resource raises HTTPInternalServerError on exception."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("DB error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            ResourceService.create_resource(
                {"name": "test"}, self.mock_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_allowed_for_mentor(self, mock_get_mongo, mock_get_config):
        """Test mentor may update a resource."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": "123",
            "name": "updated-resource",
        }
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "updated-resource"}
        updated = ResourceService.update_resource(
            "123", data, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "updated-resource")

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """Test admin may update a resource."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": "123",
            "name": "updated-resource",
        }
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "updated-resource"}
        updated = ResourceService.update_resource(
            "123", data, self.mock_admin_token, self.mock_breadcrumb
        )

        self.assertEqual(updated["name"], "updated-resource")

    @patch("src.services.resource_service.Config.get_instance")
    def test_update_resource_forbidden_without_mentor_or_admin(self, mock_get_config):
        """Test update raises HTTPForbidden without mentor/admin."""
        mock_config = MagicMock()
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        with self.assertRaises(HTTPForbidden):
            ResourceService.update_resource(
                "123", {"name": "Updated"}, self.mock_user_token, self.mock_breadcrumb
            )

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_resource raises HTTPForbidden for restricted fields."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        data = {"_id": "999", "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ResourceService.update_resource(
                "123", data, self.mock_mentor_token, self.mock_breadcrumb
            )
        self.assertIn("_id", str(context.exception))

        data = {"created": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ResourceService.update_resource(
                "123", data, self.mock_mentor_token, self.mock_breadcrumb
            )
        self.assertIn("created", str(context.exception))

        data = {"saved": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ResourceService.update_resource(
                "123", data, self.mock_mentor_token, self.mock_breadcrumb
            )
        self.assertIn("saved", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_not_found(self, mock_get_mongo, mock_get_config):
        """Test update_resource raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            ResourceService.update_resource(
                "999",
                {"name": "Updated"},
                self.mock_mentor_token,
                self.mock_breadcrumb,
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_update_resource_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test update_resource raises HTTPInternalServerError on exception."""
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        mock_config.ROLE_MENTOR = "mentor"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("DB error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            ResourceService.update_resource(
                "123",
                {"name": "Updated"},
                self.mock_mentor_token,
                self.mock_breadcrumb,
            )


if __name__ == "__main__":
    unittest.main()
