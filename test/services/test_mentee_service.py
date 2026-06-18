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
        self.mock_token = {"user_id": "mike", "roles": ["mentor"]}
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
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )

        existing = {"_id": ObjectId(MENTEE_ID), "profile_id": ObjectId(PROFILE_ID)}
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [existing]
        mock_get_mongo.return_value = mock_mongo

        result = MenteeService.get_mentee(
            PROFILE_ID, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result, existing)
        mock_mongo.get_documents.assert_called_once_with(
            "Mentee", match={"profile_id": ObjectId(PROFILE_ID)}
        )
        # No document should be created when one already exists.
        mock_mongo.create_document.assert_not_called()

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_get_mentee_creates_when_missing(self, mock_get_mongo, mock_get_config):
        """get_mentee creates a schema-valid default document when none exists."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )

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
            PROFILE_ID, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result, created_doc)
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Mentee")
        document = call_args[0][1]
        # profile_id persisted as ObjectId, sensible defaults applied.
        self.assertEqual(document["profile_id"], ObjectId(PROFILE_ID))
        self.assertEqual(document["status"], "active")
        self.assertEqual(document["created"], self.mock_breadcrumb)
        self.assertEqual(document["saved"], self.mock_breadcrumb)
        for field in ("description", "focus", "homework", "notes"):
            self.assertEqual(document[field], "")
        # name/next_appointment/schedule are omitted to satisfy pattern/format.
        self.assertNotIn("name", document)
        mock_mongo.get_document.assert_called_once_with("Mentee", MENTEE_ID)

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_get_mentee_invalid_profile_id(self, mock_get_mongo, mock_get_config):
        """get_mentee raises HTTPBadRequest for an invalid profile_id."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest):
            MenteeService.get_mentee(
                "not-an-objectid", self.mock_token, self.mock_breadcrumb
            )
        mock_mongo.get_documents.assert_not_called()

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_get_mentee_forbidden_without_mentor_role(
        self, mock_get_mongo, mock_get_config
    ):
        """Callers lacking the mentor role are denied before any DB access."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        non_mentor_token = {"user_id": "carol", "roles": ["coordinator"]}
        with self.assertRaises(HTTPForbidden):
            MenteeService.get_mentee(PROFILE_ID, non_mentor_token, self.mock_breadcrumb)
        mock_mongo.get_documents.assert_not_called()

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_update_mentee_success(self, mock_get_mongo, mock_get_config):
        """update_mentee writes $set data, stamps saved, and returns the doc."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": ObjectId(MENTEE_ID),
            "focus": "async patterns",
        }
        mock_get_mongo.return_value = mock_mongo

        data = {"focus": "async patterns", "status": "active"}
        updated = MenteeService.update_mentee(
            MENTEE_ID, data, self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["focus"], "async patterns")
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[0][0], "Mentee")
        self.assertEqual(call_args[1]["match"], {"_id": ObjectId(MENTEE_ID)})
        set_data = call_args[1]["set_data"]
        self.assertEqual(set_data["focus"], "async patterns")
        self.assertEqual(set_data["saved"], self.mock_breadcrumb)

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_update_mentee_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """update_mentee raises HTTPForbidden for restricted fields."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        for field in ("_id", "created", "saved"):
            with self.assertRaises(HTTPForbidden) as context:
                MenteeService.update_mentee(
                    MENTEE_ID,
                    {field: "x", "focus": "y"},
                    self.mock_token,
                    self.mock_breadcrumb,
                )
            self.assertIn(field, str(context.exception))
        mock_mongo.update_document.assert_not_called()

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_update_mentee_not_found(self, mock_get_mongo, mock_get_config):
        """update_mentee raises HTTPNotFound when the document is missing."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            MenteeService.update_mentee(
                MENTEE_ID, {"focus": "y"}, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn(MENTEE_ID, str(context.exception))

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_update_mentee_invalid_id(self, mock_get_mongo, mock_get_config):
        """update_mentee raises HTTPBadRequest for an invalid mentee_id."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest):
            MenteeService.update_mentee(
                "not-an-objectid", {"focus": "y"}, self.mock_token, self.mock_breadcrumb
            )
        mock_mongo.update_document.assert_not_called()

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_update_mentee_forbidden_without_mentor_role(
        self, mock_get_mongo, mock_get_config
    ):
        """update_mentee requires the mentor role before any DB access."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        non_mentor_token = {"user_id": "carol", "roles": []}
        with self.assertRaises(HTTPForbidden):
            MenteeService.update_mentee(
                MENTEE_ID, {"focus": "y"}, non_mentor_token, self.mock_breadcrumb
            )
        mock_mongo.update_document.assert_not_called()

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_get_mentee_handles_exception(self, mock_get_mongo, mock_get_config):
        """get_mentee wraps unexpected database errors as HTTPInternalServerError."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )

        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            MenteeService.get_mentee(PROFILE_ID, self.mock_token, self.mock_breadcrumb)

    @patch("src.services.mentee_service.Config.get_instance")
    @patch("src.services.mentee_service.MongoIO.get_instance")
    def test_update_mentee_handles_exception(self, mock_get_mongo, mock_get_config):
        """update_mentee wraps unexpected database errors as HTTPInternalServerError."""
        mock_get_config.return_value = MagicMock(
            spec=["MENTEE_COLLECTION_NAME", "ROLE_MENTOR", "ROLE_ADMIN"],
            MENTEE_COLLECTION_NAME="Mentee",
            ROLE_MENTOR="mentor",
            ROLE_ADMIN="admin",
        )

        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            MenteeService.update_mentee(
                MENTEE_ID, {"focus": "y"}, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.mentee_service.Config.get_instance")
    def test_check_permission_allows_mentor(self, mock_get_config):
        """A token with the mentor role passes the permission check."""
        mock_get_config.return_value = MagicMock(
            ROLE_MENTOR="mentor", ROLE_ADMIN="admin"
        )
        MenteeService._check_permission(
            {"user_id": "mike", "roles": ["mentor"]}, "read"
        )

    @patch("src.services.mentee_service.Config.get_instance")
    def test_check_permission_allows_admin(self, mock_get_config):
        """A token with the admin role passes the permission check."""
        mock_get_config.return_value = MagicMock(
            ROLE_MENTOR="mentor", ROLE_ADMIN="admin"
        )
        MenteeService._check_permission({"user_id": "ada", "roles": ["admin"]}, "read")

    @patch("src.services.mentee_service.Config.get_instance")
    def test_check_permission_denies_other_roles(self, mock_get_config):
        """A token without the mentor or admin role raises HTTPForbidden."""
        mock_get_config.return_value = MagicMock(
            ROLE_MENTOR="mentor", ROLE_ADMIN="admin"
        )
        with self.assertRaises(HTTPForbidden):
            MenteeService._check_permission(
                {"user_id": "carol", "roles": ["coordinator"]}, "read"
            )

    def test_collection_name_uses_config(self):
        """The collection name is read from Config.MENTEE_COLLECTION_NAME."""
        config = MagicMock()
        config.MENTEE_COLLECTION_NAME = "MenteeCustom"
        self.assertEqual(MenteeService._collection_name(config), "MenteeCustom")


if __name__ == "__main__":
    unittest.main()
