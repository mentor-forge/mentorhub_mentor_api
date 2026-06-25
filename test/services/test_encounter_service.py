"""
Unit tests for Encounter service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from pymongo import DESCENDING
from src.services.encounter_service import EncounterService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
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
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    # Valid 24-hex ObjectId strings reused across create tests.
    VALID_MENTOR_ID = "507f1f77bcf86cd799439011"
    VALID_MENTEE_ID = "507f1f77bcf86cd799439012"
    VALID_PLAN_ID = "507f1f77bcf86cd799439013"

    def _valid_create_data(self, **overrides):
        """Build a minimal valid create payload with the three required ids."""
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

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_success(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Test successful creation of a encounter document."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        mock_get_plan.return_value = {"_id": self.VALID_PLAN_ID, "steps": []}

        data = self._valid_create_data()

        encounter_id = EncounterService.create_encounter(
            data, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(encounter_id, "123")
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Encounter")
        created_data = call_args[0][1]
        self.assertIn("created", created_data)
        self.assertIn("saved", created_data)
        self.assertEqual(created_data["name"], "test-encounter")
        # Plan looked up via PlanService, not a direct Plan collection read.
        mock_get_plan.assert_called_once_with(
            self.VALID_PLAN_ID, self.mock_token, self.mock_breadcrumb
        )

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_agenda_from_plan_checklist(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """agenda is derived from the Plan checklist, overriding client agenda."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        mock_get_plan.return_value = {
            "_id": self.VALID_PLAN_ID,
            "steps": ["review goals", "discuss blockers"],
        }

        # Client-supplied agenda must be ignored/overwritten.
        data = self._valid_create_data(
            agenda=[{"step": "client provided", "checked": True}]
        )

        EncounterService.create_encounter(data, self.mock_token, self.mock_breadcrumb)

        created_data = mock_mongo.create_document.call_args[0][1]
        self.assertEqual(
            created_data["agenda"],
            [
                {"step": "review goals", "checked": False},
                {"step": "discuss blockers", "checked": False},
            ],
        )

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_empty_checklist_yields_empty_agenda(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """An empty/absent Plan checklist yields agenda == []."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        # Plan with no checklist/steps at all.
        mock_get_plan.return_value = {"_id": self.VALID_PLAN_ID}

        data = self._valid_create_data()
        EncounterService.create_encounter(data, self.mock_token, self.mock_breadcrumb)

        created_data = mock_mongo.create_document.call_args[0][1]
        self.assertEqual(created_data["agenda"], [])

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_missing_required_id_raises_bad_request(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Missing mentor_id/mentee_id/plan_id each raise HTTPBadRequest."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_mongo.return_value = MagicMock()
        mock_get_plan.return_value = {"_id": self.VALID_PLAN_ID, "steps": []}

        for field in ("mentor_id", "mentee_id", "plan_id"):
            data = self._valid_create_data()
            del data[field]
            with self.assertRaises(HTTPBadRequest) as context:
                EncounterService.create_encounter(
                    data, self.mock_token, self.mock_breadcrumb
                )
            self.assertIn(field, str(context.exception))

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_malformed_id_raises_bad_request(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """A non-ObjectId id raises HTTPBadRequest."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_mongo.return_value = MagicMock()
        mock_get_plan.return_value = {"_id": self.VALID_PLAN_ID, "steps": []}

        data = self._valid_create_data(plan_id="not-an-object-id")
        with self.assertRaises(HTTPBadRequest) as context:
            EncounterService.create_encounter(
                data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("plan_id", str(context.exception))

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_unknown_plan_raises_not_found(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """An unknown plan_id surfaces as HTTPNotFound (404)."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_mongo.return_value = MagicMock()

        mock_get_plan.side_effect = HTTPNotFound(f"Plan {self.VALID_PLAN_ID} not found")

        data = self._valid_create_data()
        with self.assertRaises(HTTPNotFound):
            EncounterService.create_encounter(
                data, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_removes_id(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Test that _id is removed from data before creation."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        mock_get_plan.return_value = {"_id": self.VALID_PLAN_ID, "steps": []}

        data = self._valid_create_data(_id="should-be-removed")

        EncounterService.create_encounter(data, self.mock_token, self.mock_breadcrumb)

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounter_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific encounter document."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "encounter1",
        }
        mock_get_mongo.return_value = mock_mongo

        result = EncounterService.get_encounter(
            "123", self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Encounter", "123")

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounter_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_encounter raises HTTPNotFound when document not found."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            EncounterService.get_encounter("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_success(self, mock_get_mongo, mock_get_config):
        """Test successful update of a encounter document."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": "123",
            "name": "updated-encounter",
        }
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "updated-encounter", "description": "Updated"}

        updated = EncounterService.update_encounter(
            "123", data, self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "updated-encounter")
        mock_mongo.update_document.assert_called_once()
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[1]["document_id"], "123")
        set_data = call_args[1]["set_data"]
        self.assertIn("saved", set_data)
        self.assertEqual(set_data["name"], "updated-encounter")

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_encounter raises HTTPForbidden for restricted fields."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "999", "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            EncounterService.update_encounter(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("_id", str(context.exception))

        data = {"created": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            EncounterService.update_encounter(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("created", str(context.exception))

        data = {"saved": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            EncounterService.update_encounter(
                "123", data, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("saved", str(context.exception))

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_not_found(self, mock_get_mongo, mock_get_config):
        """Test update_encounter raises HTTPNotFound when document not found."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            EncounterService.update_encounter(
                "999", {"name": "Updated"}, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_uses_breadcrumb_directly(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_encounter uses breadcrumb directly for saved field."""
        mock_config = _make_config()
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

        result = EncounterService.update_encounter(
            "123", {"name": "updated"}, self.mock_token, breadcrumb
        )

        self.assertIsNotNone(result)
        call_args = mock_mongo.update_document.call_args
        set_data = call_args[1]["set_data"]
        self.assertEqual(set_data["saved"], breadcrumb)
        self.assertEqual(set_data["saved"]["from_ip"], "192.168.1.1")

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_create_encounter_handles_exception(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Test create_encounter handles database exceptions."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        mock_get_plan.return_value = {"_id": self.VALID_PLAN_ID, "steps": []}

        with self.assertRaises(HTTPInternalServerError):
            EncounterService.create_encounter(
                self._valid_create_data(), self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounter_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_encounter handles database exceptions."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            EncounterService.get_encounter("123", self.mock_token, self.mock_breadcrumb)

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test update_encounter handles database exceptions."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            EncounterService.update_encounter(
                "123", {"name": "updated"}, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_recent_encounter_returns_summary(
        self, mock_get_mongo, mock_get_config
    ):
        """Most recent encounter is summarized for the dashboard card."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mentee_id = ObjectId("507f1f77bcf86cd799439011")
        encounter_id = ObjectId("507f1f77bcf86cd7994390aa")
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {
                "_id": encounter_id,
                "mentee_id": mentee_id,
                "date": "2025-02-01T00:00:00Z",
                "tldr": "great session",
                "summary": "covered async patterns",
                "notes": "extra field not returned in summary",
            }
        ]
        mock_get_mongo.return_value = mock_mongo

        result = EncounterService.get_recent_encounter(
            mentee_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(
            result,
            {
                "_id": encounter_id,
                "date": "2025-02-01T00:00:00Z",
                "tldr": "great session",
                "summary": "covered async patterns",
            },
        )

        # The latest encounter is requested (sorted by date descending) and
        # matched by mentee id.
        mock_mongo.get_documents.assert_called_once()
        args, kwargs = mock_mongo.get_documents.call_args
        self.assertEqual(args[0], "Encounter")
        self.assertEqual(kwargs["match"], {"mentee_id": mentee_id})
        self.assertEqual(kwargs["sort_by"], [("date", DESCENDING)])

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_recent_encounter_none_when_no_encounters(
        self, mock_get_mongo, mock_get_config
    ):
        """Return None when the mentee has no encounters."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        result = EncounterService.get_recent_encounter(
            ObjectId("507f1f77bcf86cd799439011"),
            self.mock_token,
            self.mock_breadcrumb,
        )

        self.assertIsNone(result)

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounters_for_mentee_returns_sorted_list(
        self, mock_get_mongo, mock_get_config
    ):
        """All of a mentee's encounters are returned, most recent first."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        newer = {"_id": ObjectId("507f1f77bcf86cd7994390aa"), "date": "2025-03-01"}
        older = {"_id": ObjectId("507f1f77bcf86cd7994390a1"), "date": "2025-01-01"}
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [newer, older]
        mock_get_mongo.return_value = mock_mongo

        mentee_id = ObjectId("507f1f77bcf86cd799439011")
        result = EncounterService.get_encounters_for_mentee(
            mentee_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result, [newer, older])
        mock_mongo.get_documents.assert_called_once()
        args, kwargs = mock_mongo.get_documents.call_args
        self.assertEqual(args[0], "Encounter")
        self.assertEqual(kwargs["match"], {"mentee_id": mentee_id})
        self.assertEqual(kwargs["sort_by"], [("date", DESCENDING)])

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounters_for_mentee_converts_string_id(
        self, mock_get_mongo, mock_get_config
    ):
        """A string mentee id is normalized to ObjectId for the direct query."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        mentee_id = "507f1f77bcf86cd799439011"
        EncounterService.get_encounters_for_mentee(
            mentee_id, self.mock_token, self.mock_breadcrumb
        )

        args, kwargs = mock_mongo.get_documents.call_args
        self.assertEqual(kwargs["match"], {"mentee_id": ObjectId(mentee_id)})

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounters_for_mentee_keeps_non_objectid_value(
        self, mock_get_mongo, mock_get_config
    ):
        """A non-ObjectId mentee id is matched as-is without raising."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        EncounterService.get_encounters_for_mentee(
            "not-an-object-id", self.mock_token, self.mock_breadcrumb
        )

        args, kwargs = mock_mongo.get_documents.call_args
        self.assertEqual(kwargs["match"], {"mentee_id": "not-an-object-id"})

    # ------------------------------------------------------------------
    # RBAC: read (get_encounter)
    # ------------------------------------------------------------------

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounter_allowed_for_mentor(self, mock_get_mongo, mock_get_config):
        """A mentor may read any encounter (no ownership check on read)."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "name": "encounter1"}
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "mentor_user", "roles": ["mentor"]}
        result = EncounterService.get_encounter("123", token, self.mock_breadcrumb)

        self.assertEqual(result["_id"], "123")

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounter_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """An admin may read any encounter."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "name": "encounter1"}
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "admin_user", "roles": ["admin"]}
        result = EncounterService.get_encounter("123", token, self.mock_breadcrumb)

        self.assertEqual(result["_id"], "123")

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_get_encounter_denied_for_other_role(self, mock_get_mongo, mock_get_config):
        """A caller with neither mentor nor admin role is denied (403)."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "mentee_user", "roles": ["mentee"]}
        with self.assertRaises(HTTPForbidden):
            EncounterService.get_encounter("123", token, self.mock_breadcrumb)

        mock_mongo.get_document.assert_not_called()

    # ------------------------------------------------------------------
    # RBAC: update (update_encounter) — owner-or-admin
    # ------------------------------------------------------------------

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """An admin may update any encounter without an ownership check."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "mentor_id": ObjectId("507f1f77bcf86cd799439011"),
        }
        mock_mongo.update_document.return_value = {"_id": "123", "name": "updated"}
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "admin_user", "roles": ["admin"]}
        updated = EncounterService.update_encounter(
            "123", {"name": "updated"}, token, self.mock_breadcrumb
        )

        self.assertEqual(updated["name"], "updated")
        # Admin path must not resolve a caller profile for ownership.
        mock_mongo.get_documents.assert_not_called()

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_allowed_for_owning_mentor(
        self, mock_get_mongo, mock_get_config
    ):
        """The owning mentor (Profile _id == mentor_id) may update."""
        mock_get_config.return_value = _make_config()

        mentor_object_id = ObjectId("507f1f77bcf86cd799439011")
        mock_mongo = MagicMock()
        # Encounter stores mentor_id as a STRING; the caller Profile _id is an
        # ObjectId of the same value, proving the comparison is string-based.
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "mentor_id": str(mentor_object_id),
        }
        mock_mongo.get_documents.return_value = [
            {"_id": mentor_object_id, "name": "mike"}
        ]
        mock_mongo.update_document.return_value = {"_id": "123", "name": "updated"}
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "mike", "roles": ["mentor"]}
        updated = EncounterService.update_encounter(
            "123", {"name": "updated"}, token, self.mock_breadcrumb
        )

        self.assertEqual(updated["name"], "updated")
        mock_mongo.get_documents.assert_called_once_with(
            "Profile", match={"name": "mike"}
        )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_denied_for_non_owning_mentor(
        self, mock_get_mongo, mock_get_config
    ):
        """A mentor who does not own the encounter is denied (403)."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "mentor_id": ObjectId("507f1f77bcf86cd799439011"),
        }
        mock_mongo.get_documents.return_value = [
            {"_id": ObjectId("507f1f77bcf86cd7994390ff"), "name": "other"}
        ]
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "other", "roles": ["mentor"]}
        with self.assertRaises(HTTPForbidden):
            EncounterService.update_encounter(
                "123", {"name": "updated"}, token, self.mock_breadcrumb
            )

        mock_mongo.update_document.assert_not_called()

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_denied_for_other_role(
        self, mock_get_mongo, mock_get_config
    ):
        """A caller with neither mentor nor admin role is denied (403)."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "mentee_user", "roles": ["mentee"]}
        with self.assertRaises(HTTPForbidden):
            EncounterService.update_encounter(
                "123", {"name": "updated"}, token, self.mock_breadcrumb
            )

        mock_mongo.get_document.assert_not_called()
        mock_mongo.update_document.assert_not_called()

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_missing_yields_not_found(
        self, mock_get_mongo, mock_get_config
    ):
        """A missing encounter yields 404 before the ownership check."""
        mock_get_config.return_value = _make_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        token = {"user_id": "mike", "roles": ["mentor"]}
        with self.assertRaises(HTTPNotFound) as context:
            EncounterService.update_encounter(
                "999", {"name": "updated"}, token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

        # 404 short-circuits before resolving ownership or updating.
        mock_mongo.get_documents.assert_not_called()
        mock_mongo.update_document.assert_not_called()


if __name__ == "__main__":
    unittest.main()
