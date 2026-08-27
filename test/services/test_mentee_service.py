"""
Unit tests for Mentee service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.mentee_service import MenteeService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)

PROFILE_ID = "507f1f77bcf86cd799439011"
MENTEE_ID = "507f1f77bcf86cd7994390aa"


class TestMenteeService(unittest.TestCase):
    """Test cases for MenteeService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_mentor_token = {"user_id": "mike", "roles": ["mentor"]}
        self.mock_admin_token = {"user_id": "admin", "roles": ["admin"]}
        self.mock_user_token = {"user_id": "regular", "roles": ["user"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "mike",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_get_mentee_existing(self, mock_get_mongo, mock_get_config):
        """get_mentee returns the existing document when one is found."""
        mock_config = MagicMock()
        mock_config.MENTEE_COLLECTION_NAME = "Mentee"
        mock_config.ROLE_MENTOR = "mentor"
        mock_config.ROLE_ADMIN = "admin"
        mock_get_config.return_value = mock_config

        existing = {"_id": ObjectId(MENTEE_ID), "profile_id": ObjectId(PROFILE_ID)}
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [existing]
        mock_get_mongo.return_value = mock_mongo

        result = MenteeService.get_mentee(
            PROFILE_ID, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertEqual(result, existing)
        mock_mongo.create_document.assert_not_called()

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_get_mentee_creates_when_missing_for_mentor(
        self, mock_get_mongo, mock_get_config
    ):
        """get_mentee creates a schema-valid default document when none exists."""
        mock_config = MagicMock()
        mock_config.MENTEE_COLLECTION_NAME = "Mentee"
        mock_config.ROLE_MENTOR = "mentor"
        mock_config.ROLE_ADMIN = "admin"
        mock_get_config.return_value = mock_config

        created_doc = {
            "_id": ObjectId(MENTEE_ID),
            "profile_id": ObjectId(PROFILE_ID),
            "status": "active",
        }
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_mongo.create_document.return_value = MENTEE_ID
        mock_mongo.get_document.return_value = created_doc
        mock_get_mongo.return_value = mock_mongo

        result = MenteeService.get_mentee(
            PROFILE_ID, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertEqual(result, created_doc)
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Mentee")
        document = call_args[0][1]
        self.assertEqual(document["profile_id"], ObjectId(PROFILE_ID))
        self.assertEqual(document["status"], "active")
        self.assertEqual(document["created"], self.mock_breadcrumb)
        self.assertEqual(document["saved"], self.mock_breadcrumb)

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_get_mentee_creates_when_missing_for_admin(
        self, mock_get_mongo, mock_get_config
    ):
        """get_mentee creates document for admin when missing."""
        mock_config = MagicMock()
        mock_config.MENTEE_COLLECTION_NAME = "Mentee"
        mock_config.ROLE_MENTOR = "mentor"
        mock_config.ROLE_ADMIN = "admin"
        mock_get_config.return_value = mock_config

        created_doc = {
            "_id": ObjectId(MENTEE_ID),
            "profile_id": ObjectId(PROFILE_ID),
            "status": "active",
        }
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_mongo.create_document.return_value = MENTEE_ID
        mock_mongo.get_document.return_value = created_doc
        mock_get_mongo.return_value = mock_mongo

        result = MenteeService.get_mentee(
            PROFILE_ID, self.mock_admin_token, self.mock_breadcrumb
        )

        self.assertEqual(result, created_doc)

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_get_mentee_missing_forbidden_for_non_mentor(
        self, mock_get_mongo, mock_get_config
    ):
        """Non-mentor attempting to create-if-missing gets HTTPForbidden."""
        mock_config = MagicMock()
        mock_config.MENTEE_COLLECTION_NAME = "Mentee"
        mock_config.ROLE_MENTOR = "mentor"
        mock_config.ROLE_ADMIN = "admin"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            MenteeService.get_mentee(
                PROFILE_ID, self.mock_user_token, self.mock_breadcrumb
            )

    def test_get_mentee_invalid_profile_id(self):
        """Invalid profile_id raises HTTPBadRequest."""
        with self.assertRaises(HTTPBadRequest):
            MenteeService.get_mentee(
                "invalid-id", self.mock_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_update_mentee_success(self, mock_get_mongo, mock_get_config):
        """update_mentee successfully updates fields."""
        mock_config = MagicMock()
        mock_config.MENTEE_COLLECTION_NAME = "Mentee"
        mock_config.ROLE_MENTOR = "mentor"
        mock_config.ROLE_ADMIN = "admin"
        mock_get_config.return_value = mock_config

        updated_doc = {
            "_id": ObjectId(MENTEE_ID),
            "profile_id": ObjectId(PROFILE_ID),
            "notes": "Great progress",
        }
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = updated_doc
        mock_get_mongo.return_value = mock_mongo

        result = MenteeService.update_mentee(
            MENTEE_ID,
            {"notes": "Great progress"},
            self.mock_mentor_token,
            self.mock_breadcrumb,
        )

        self.assertEqual(result, updated_doc)
        mock_mongo.update_document.assert_called_once()
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[0][0], "Mentee")
        self.assertEqual(call_args[1]["match"], {"_id": ObjectId(MENTEE_ID)})
        set_data = call_args[1]["set_data"]
        self.assertEqual(set_data["notes"], "Great progress")
        self.assertEqual(set_data["saved"], self.mock_breadcrumb)

    @patch("src.services.mentee_service.Config.get_instance")
    def test_update_mentee_forbidden_without_mentor_role(self, mock_get_config):
        """update_mentee raises HTTPForbidden for non-mentor / non-admin."""
        mock_config = MagicMock()
        mock_config.ROLE_MENTOR = "mentor"
        mock_config.ROLE_ADMIN = "admin"
        mock_get_config.return_value = mock_config

        with self.assertRaises(HTTPForbidden):
            MenteeService.update_mentee(
                MENTEE_ID,
                {"notes": "Updated"},
                self.mock_user_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.mentee_service.Config.get_instance")
    def test_update_mentee_prevent_restricted_fields(self, mock_get_config):
        """update_mentee rejects restricted fields."""
        mock_config = MagicMock()
        mock_config.ROLE_MENTOR = "mentor"
        mock_config.ROLE_ADMIN = "admin"
        mock_get_config.return_value = mock_config

        for field in ("_id", "created", "saved"):
            with self.assertRaises(HTTPForbidden):
                MenteeService.update_mentee(
                    MENTEE_ID,
                    {field: "disallowed"},
                    self.mock_mentor_token,
                    self.mock_breadcrumb,
                )

    def test_update_mentee_invalid_id(self):
        """update_mentee raises HTTPBadRequest for invalid id."""
        with self.assertRaises(HTTPBadRequest):
            MenteeService.update_mentee(
                "invalid-id",
                {"notes": "Test"},
                self.mock_mentor_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_update_mentee_not_found(self, mock_get_mongo, mock_get_config):
        """update_mentee raises HTTPNotFound when document doesn't exist."""
        mock_config = MagicMock()
        mock_config.MENTEE_COLLECTION_NAME = "Mentee"
        mock_config.ROLE_MENTOR = "mentor"
        mock_config.ROLE_ADMIN = "admin"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            MenteeService.update_mentee(
                MENTEE_ID,
                {"notes": "Test"},
                self.mock_mentor_token,
                self.mock_breadcrumb,
            )


if __name__ == "__main__":
    unittest.main()
