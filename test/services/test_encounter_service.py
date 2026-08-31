"""
Unit tests for Encounter service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.encounter_service import EncounterService
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


def _make_config():
    """Build a config mock exposing the names/role constants the service reads."""
    mock_config = MagicMock()
    mock_config.ENCOUNTER_COLLECTION_NAME = "Encounter"
    mock_config.PROFILE_COLLECTION_NAME = "Profile"
    mock_config.ROLE_MENTOR = "mentor"
    mock_config.ROLE_ADMIN = "admin"
    return mock_config


class TestEncounterService(unittest.TestCase):
    """Test cases for EncounterService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_admin_token = {"user_id": "admin_user", "roles": ["admin"]}
        self.mock_mentor_token = {
            "user_id": "mentor_user",
            "roles": ["mentor"],
            "profile_id": "507f1f77bcf86cd799439011",
        }
        self.mock_other_mentor_token = {
            "user_id": "other_mentor",
            "roles": ["mentor"],
            "profile_id": "507f1f77bcf86cd799439099",
        }
        self.mock_user_token = {"user_id": "regular_user", "roles": ["user"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    VALID_MENTOR_ID = "507f1f77bcf86cd799439011"
    VALID_MENTEE_ID = "507f1f77bcf86cd799439012"
    VALID_PLAN_ID = "507f1f77bcf86cd799439013"

    def _valid_create_data(self, **overrides):
        data = {
            "name": "test-encounter",
            "description": "Test encounter",
            "status": "active",
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "plan_id": self.VALID_PLAN_ID,
        }
        data.update(overrides)
        return data

    def test_inherited_methods_exist(self):
        """Assert inherited GET methods exist on the subclass."""
        self.assertTrue(callable(getattr(EncounterService, "get_encounter", None)))
        self.assertTrue(
            callable(getattr(EncounterService, "get_encounters_for_mentee", None))
        )
        self.assertTrue(
            callable(getattr(EncounterService, "get_recent_encounter", None))
        )

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_allowed_for_mentor_with_agenda(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Mentor creates encounter; agenda is populated from plan checklist."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "enc-123"
        mock_get_mongo.return_value = mock_mongo

        mock_get_plan.return_value = {
            "_id": self.VALID_PLAN_ID,
            "steps": ["Step 1", "Step 2"],
        }

        data = self._valid_create_data()
        encounter_id = EncounterService.create_encounter(
            data, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertEqual(encounter_id, "enc-123")
        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertEqual(
            created_data["agenda"],
            [
                {"step": "Step 1", "checked": False},
                {"step": "Step 2", "checked": False},
            ],
        )

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_allowed_for_admin(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Admin creates encounter."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "enc-123"
        mock_get_mongo.return_value = mock_mongo

        mock_get_plan.return_value = {"_id": self.VALID_PLAN_ID, "checklist": ["A"]}

        data = self._valid_create_data()
        encounter_id = EncounterService.create_encounter(
            data, self.mock_admin_token, self.mock_breadcrumb
        )

        self.assertEqual(encounter_id, "enc-123")

    @patch("src.services.encounter_service.Config.get_instance")
    def test_create_encounter_forbidden_without_mentor_or_admin(self, mock_get_config):
        """Non-privileged user cannot create an encounter."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        with self.assertRaises(HTTPForbidden):
            EncounterService.create_encounter(
                self._valid_create_data(),
                self.mock_user_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    def test_create_encounter_propagates_plan_not_found(
        self, mock_get_config, mock_get_plan
    ):
        """Missing Plan raises HTTPNotFound."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_plan.side_effect = HTTPNotFound("Plan not found")

        with self.assertRaises(HTTPNotFound):
            EncounterService.create_encounter(
                self._valid_create_data(),
                self.mock_mentor_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_handles_exception(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Exceptions during create raise HTTPInternalServerError."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_plan.return_value = {"steps": []}
        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("DB failure")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            EncounterService.create_encounter(
                self._valid_create_data(),
                self.mock_mentor_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_allowed_for_owning_mentor(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """Owning mentor may update their encounter."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-123",
            "mentor_id": ObjectId(self.VALID_MENTOR_ID),
        }
        mock_mongo.update_document.return_value = {
            "_id": "enc-123",
            "notes": "Updated",
        }
        mock_get_mongo.return_value = mock_mongo

        updated = EncounterService.update_encounter(
            "enc-123",
            {"notes": "Updated"},
            self.mock_mentor_token,
            self.mock_breadcrumb,
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["notes"], "Updated")

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """Admin may update any encounter."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-123",
            "mentor_id": ObjectId(self.VALID_MENTOR_ID),
        }
        mock_mongo.update_document.return_value = {
            "_id": "enc-123",
            "notes": "Updated",
        }
        mock_get_mongo.return_value = mock_mongo

        updated = EncounterService.update_encounter(
            "enc-123",
            {"notes": "Updated"},
            self.mock_admin_token,
            self.mock_breadcrumb,
        )

        self.assertIsNotNone(updated)

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_forbidden_for_different_mentor(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """A mentor cannot update an encounter they do not own."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_get_profile.return_value = {"_id": "507f1f77bcf86cd799439099"}

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-123",
            "mentor_id": ObjectId(self.VALID_MENTOR_ID),
        }
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            EncounterService.update_encounter(
                "enc-123",
                {"notes": "Updated"},
                self.mock_other_mentor_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.encounter_service.Config.get_instance")
    def test_update_encounter_forbidden_without_mentor_or_admin(self, mock_get_config):
        """Regular user cannot update encounter."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        with self.assertRaises(HTTPForbidden):
            EncounterService.update_encounter(
                "enc-123",
                {"notes": "Updated"},
                self.mock_user_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_not_found(self, mock_get_mongo, mock_get_config):
        """Missing encounter raises HTTPNotFound."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            EncounterService.update_encounter(
                "enc-missing",
                {"notes": "Updated"},
                self.mock_admin_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Restricted fields on update raise HTTPForbidden."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-123",
            "mentor_id": ObjectId(self.VALID_MENTOR_ID),
        }
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            EncounterService.update_encounter(
                "enc-123",
                {"_id": "new-id"},
                self.mock_admin_token,
                self.mock_breadcrumb,
            )


if __name__ == "__main__":
    unittest.main()
