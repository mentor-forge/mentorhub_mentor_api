"""
Unit tests for Encounter service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
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
    mock_config.CUSTOMER_COLLECTION_NAME = "Customer"
    mock_config.EVENT_COLLECTION_NAME = "Event"
    mock_config.EVENT_TYPE_ENCOUNTER = "encounter"
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
        """Owning mentor may update their active encounter with allowed fields."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-123",
            "mentor_id": ObjectId(self.VALID_MENTOR_ID),
            "status": "active",
        }
        mock_mongo.update_document.return_value = {
            "_id": "enc-123",
            "summary": "Updated summary",
            "status": "active",
        }
        mock_get_mongo.return_value = mock_mongo

        updated = EncounterService.update_encounter(
            "enc-123",
            {"summary": "Updated summary"},
            self.mock_mentor_token,
            self.mock_breadcrumb,
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["summary"], "Updated summary")

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_allowed_for_admin(self, mock_get_mongo, mock_get_config):
        """Admin may update any active encounter with allowed fields."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-123",
            "mentor_id": ObjectId(self.VALID_MENTOR_ID),
            "status": "active",
        }
        mock_mongo.update_document.return_value = {
            "_id": "enc-123",
            "summary": "Updated summary",
            "status": "active",
        }
        mock_get_mongo.return_value = mock_mongo

        updated = EncounterService.update_encounter(
            "enc-123",
            {"summary": "Updated summary"},
            self.mock_admin_token,
            self.mock_breadcrumb,
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["summary"], "Updated summary")

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
            "status": "active",
        }
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            EncounterService.update_encounter(
                "enc-123",
                {"summary": "Updated summary"},
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
                {"summary": "Updated summary"},
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
                {"summary": "Updated summary"},
                self.mock_admin_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Disallowed fields on update raise HTTPForbidden."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-123",
            "mentor_id": ObjectId(self.VALID_MENTOR_ID),
            "status": "active",
        }
        mock_get_mongo.return_value = mock_mongo

        for field in [
            "_id",
            "created",
            "saved",
            "status",
            "mentor_id",
            "mentee_id",
            "plan_id",
            "appointment",
            "notes",
        ]:
            with self.assertRaises(HTTPForbidden):
                EncounterService.update_encounter(
                    "enc-123",
                    {field: "disallowed"},
                    self.mock_admin_token,
                    self.mock_breadcrumb,
                )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_forbidden_when_not_active(
        self, mock_get_mongo, mock_get_config
    ):
        """Updating encounter when status is not active raises HTTPForbidden."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        for inactive_status in ["scheduled", "complete", "archived"]:
            mock_mongo.get_document.return_value = {
                "_id": "enc-123",
                "mentor_id": ObjectId(self.VALID_MENTOR_ID),
                "status": inactive_status,
            }
            mock_get_mongo.return_value = mock_mongo

            with self.assertRaises(HTTPForbidden):
                EncounterService.update_encounter(
                    "enc-123",
                    {"summary": "Updated summary"},
                    self.mock_admin_token,
                    self.mock_breadcrumb,
                )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_update_encounter_allowed_fields_and_agenda(
        self, mock_get_mongo, mock_get_config
    ):
        """Updating agenda, transcript, summary, and tldr succeeds."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-123",
            "mentor_id": ObjectId(self.VALID_MENTOR_ID),
            "status": "active",
        }
        mock_mongo.update_document.return_value = {
            "_id": "enc-123",
            "status": "active",
            "summary": "Summary",
            "tldr": "TLDR",
            "transcript": "Meeting text",
            "agenda": [{"step": "Step 1", "checked": True}],
        }
        mock_get_mongo.return_value = mock_mongo

        update_payload = {
            "summary": "Summary",
            "tldr": "TLDR",
            "transcript": "Meeting text",
            "agenda": [{"step": "Step 1", "checked": True}],
        }
        result = EncounterService.update_encounter(
            "enc-123",
            update_payload,
            self.mock_admin_token,
            self.mock_breadcrumb,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["summary"], "Summary")
        self.assertEqual(result["agenda"][0]["checked"], True)

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_enrich_encounter_populates_display_names(
        self, mock_get_mongo, mock_get_config
    ):
        """Encounter document is enriched with mentor_name and mentee_name."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()

        def mock_get_doc(collection, doc_id):
            if str(doc_id) == self.VALID_MENTOR_ID:
                return {"_id": doc_id, "display_name": "Jane Mentor"}
            if str(doc_id) == self.VALID_MENTOR_ID:
                return {"_id": doc_id, "display_name": "Jane Mentor"}
            if str(doc_id) == self.VALID_MENTEE_ID:
                return {"_id": doc_id, "display_name": "Bob Mentee"}
            return None

        mock_mongo.get_document.side_effect = mock_get_doc
        mock_get_mongo.return_value = mock_mongo

        raw_encounter = {
            "_id": "enc-1",
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
        }
        enriched = EncounterService._enrich_encounter(raw_encounter)
        self.assertEqual(enriched["mentor_name"], "Jane Mentor")
        self.assertEqual(enriched["mentee_name"], "Bob Mentee")

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_enrich_encounter_handles_missing_profiles(
        self, mock_get_mongo, mock_get_config
    ):
        """Encounter enrichment sets names to None when profile not found."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        raw_encounter = {
            "_id": "enc-1",
            "mentor_id": "507f1f77bcf86cd799439099",
            "mentee_id": "507f1f77bcf86cd799439098",
        }
        enriched = EncounterService._enrich_encounter(raw_encounter)
        self.assertIsNone(enriched["mentor_name"])
        self.assertIsNone(enriched["mentee_name"])

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_enrich_encounters_list(self, mock_get_mongo, mock_get_config):
        """List of encounters is enriched with names."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = lambda coll, doc_id: {
            "_id": doc_id,
            "display_name": f"Name_{doc_id}",
        }
        mock_get_mongo.return_value = mock_mongo

        encounters = [
            {
                "_id": "enc-1",
                "mentor_id": self.VALID_MENTOR_ID,
                "mentee_id": self.VALID_MENTEE_ID,
            },
            {
                "_id": "enc-2",
                "mentor_id": self.VALID_MENTOR_ID,
                "mentee_id": self.VALID_MENTEE_ID,
            },
        ]
        enriched_list = EncounterService._enrich_encounters(encounters)
        self.assertEqual(len(enriched_list), 2)
        self.assertEqual(
            enriched_list[0]["mentor_name"], f"Name_{self.VALID_MENTOR_ID}"
        )
        self.assertEqual(
            enriched_list[0]["mentee_name"], f"Name_{self.VALID_MENTEE_ID}"
        )
        self.assertEqual(
            enriched_list[1]["mentor_name"], f"Name_{self.VALID_MENTOR_ID}"
        )

    @patch("api_utils.services.EncounterService.get_encounter")
    @patch("src.services.encounter_service.EncounterService._enrich_encounter")
    def test_get_encounter_calls_enrichment(self, mock_enrich, mock_super_get):
        """get_encounter delegates to super and enriches."""
        mock_super_get.return_value = {"_id": "enc-1"}
        mock_enrich.return_value = {
            "_id": "enc-1",
            "mentor_name": "M",
            "mentee_name": "E",
        }

        result = EncounterService.get_encounter(
            "enc-1", self.mock_admin_token, self.mock_breadcrumb
        )
        mock_super_get.assert_called_once_with(
            "enc-1", self.mock_admin_token, self.mock_breadcrumb
        )
        mock_enrich.assert_called_once_with({"_id": "enc-1"})
        self.assertEqual(result["mentor_name"], "M")

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_schedule_encounters_success_mentor(
        self, mock_get_mongo, mock_get_config, mock_get_plan, mock_get_profile
    ):
        """Owning mentor schedules recurring encounters successfully."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}
        mock_get_plan.return_value = {
            "_id": self.VALID_PLAN_ID,
            "steps": ["Step 1", "Step 2"],
        }

        created_docs = []
        mock_mongo = MagicMock()

        def mock_create(coll, doc):
            doc_id = f"enc-{len(created_docs) + 1}"
            stored = dict(doc)
            stored["_id"] = doc_id
            created_docs.append(stored)
            return doc_id

        def mock_get_doc(coll, doc_id):
            if str(doc_id) == self.VALID_MENTOR_ID:
                return {"_id": doc_id, "display_name": "Jane Mentor"}
            if str(doc_id) == self.VALID_MENTEE_ID:
                return {"_id": doc_id, "display_name": "Bob Mentee"}
            for d in created_docs:
                if str(d.get("_id")) == str(doc_id):
                    return dict(d)
            return None

        mock_mongo.create_document.side_effect = mock_create
        mock_mongo.get_document.side_effect = mock_get_doc
        mock_get_mongo.return_value = mock_mongo

        payload = {
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "plan_id": self.VALID_PLAN_ID,
            "start_date": "2024-02-01",  # Thursday
            "day_of_week": 1,  # Monday -> 2024-02-05
            "time_of_day": "14:00",
            "recurrence_days": 7,
            "count": 3,
        }

        encounters = EncounterService.schedule_encounters(
            payload, self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertEqual(len(encounters), 3)
        self.assertEqual(mock_mongo.create_document.call_count, 3)

        # Check first encounter (adjusted to Monday Feb 5)
        self.assertEqual(encounters[0]["appointment"]["from"], "2024-02-05T14:00:00Z")
        self.assertEqual(encounters[0]["appointment"]["to"], "2024-02-05T15:00:00Z")
        self.assertEqual(encounters[0]["status"], "scheduled")
        self.assertEqual(len(encounters[0]["agenda"]), 2)
        self.assertEqual(encounters[0]["agenda"][0]["step"], "Step 1")
        self.assertFalse(encounters[0]["agenda"][0]["checked"])
        self.assertEqual(encounters[0]["mentor_name"], "Jane Mentor")
        self.assertEqual(encounters[0]["mentee_name"], "Bob Mentee")

        # Check second encounter (Feb 12)
        self.assertEqual(encounters[1]["appointment"]["from"], "2024-02-12T14:00:00Z")
        # Check third encounter (Feb 19)
        self.assertEqual(encounters[2]["appointment"]["from"], "2024-02-19T14:00:00Z")

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_schedule_encounters_success_admin(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Admin schedules recurring encounters for any mentor."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_plan.return_value = {
            "_id": self.VALID_PLAN_ID,
            "checklist": ["Check 1"],
        }

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "enc-1"
        mock_mongo.get_document.return_value = {
            "_id": "enc-1",
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "status": "scheduled",
        }
        mock_get_mongo.return_value = mock_mongo

        payload = {
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "plan_id": self.VALID_PLAN_ID,
            "start_date": "2024-02-01",
            "time_of_day": "10:30",
            "count": 1,
        }

        encounters = EncounterService.schedule_encounters(
            payload, self.mock_admin_token, self.mock_breadcrumb
        )
        self.assertEqual(len(encounters), 1)

    @patch("src.services.encounter_service.PlanService.get_plan")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_schedule_encounters_defaults(
        self, mock_get_mongo, mock_get_config, mock_get_plan
    ):
        """Omitting day_of_week and recurrence_days uses start_date and 7 days."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_plan.return_value = {"_id": self.VALID_PLAN_ID}

        created = []
        mock_mongo = MagicMock()

        def mock_create(coll, doc):
            created.append(doc)
            return "id"

        mock_mongo.create_document.side_effect = mock_create
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        payload = {
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "plan_id": self.VALID_PLAN_ID,
            "start_date": "2024-02-01",  # Thursday
            "time_of_day": "09:00",
            "count": 2,
        }

        encounters = EncounterService.schedule_encounters(
            payload, self.mock_admin_token, self.mock_breadcrumb
        )
        self.assertEqual(len(encounters), 2)
        # Default start date is Feb 01 (since day_of_week defaulted to Thursday)
        self.assertEqual(created[0]["appointment"]["from"], "2024-02-01T09:00:00Z")
        self.assertEqual(created[1]["appointment"]["from"], "2024-02-08T09:00:00Z")

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    def test_schedule_encounters_forbidden_other_mentor(
        self, mock_get_config, mock_get_profile
    ):
        """Mentor cannot schedule encounters for another mentor."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": "different-mentor-id"}

        payload = {
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "plan_id": self.VALID_PLAN_ID,
            "start_date": "2024-02-01",
            "time_of_day": "14:00",
            "count": 1,
        }

        with self.assertRaises(HTTPForbidden):
            EncounterService.schedule_encounters(
                payload, self.mock_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.encounter_service.Config.get_instance")
    def test_schedule_encounters_forbidden_user_role(self, mock_get_config):
        """User role cannot schedule encounters."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        payload = {
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "plan_id": self.VALID_PLAN_ID,
            "start_date": "2024-02-01",
            "time_of_day": "14:00",
            "count": 1,
        }

        with self.assertRaises(HTTPForbidden):
            EncounterService.schedule_encounters(
                payload, self.mock_user_token, self.mock_breadcrumb
            )

    @patch("src.services.encounter_service.Config.get_instance")
    def test_schedule_encounters_missing_and_invalid_fields(self, mock_get_config):
        """Validation errors raise HTTPBadRequest."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config

        base_valid = {
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "plan_id": self.VALID_PLAN_ID,
            "start_date": "2024-02-01",
            "time_of_day": "14:00",
            "count": 1,
        }

        # Missing required field
        for req in [
            "mentor_id",
            "mentee_id",
            "plan_id",
            "start_date",
            "time_of_day",
            "count",
        ]:
            payload = dict(base_valid)
            del payload[req]
            with self.assertRaises(HTTPBadRequest):
                EncounterService.schedule_encounters(
                    payload, self.mock_admin_token, self.mock_breadcrumb
                )

        # Invalid start_date
        bad_date = dict(base_valid, start_date="invalid-date")
        with self.assertRaises(HTTPBadRequest):
            EncounterService.schedule_encounters(
                bad_date, self.mock_admin_token, self.mock_breadcrumb
            )

        # Invalid time_of_day
        bad_time = dict(base_valid, time_of_day="25:99")
        with self.assertRaises(HTTPBadRequest):
            EncounterService.schedule_encounters(
                bad_time, self.mock_admin_token, self.mock_breadcrumb
            )

        # Invalid count
        for bad_count in [0, -1, "not-int"]:
            payload = dict(base_valid, count=bad_count)
            with self.assertRaises(HTTPBadRequest):
                EncounterService.schedule_encounters(
                    payload, self.mock_admin_token, self.mock_breadcrumb
                )

        # Invalid day_of_week
        bad_dow = dict(base_valid, day_of_week=7)
        with self.assertRaises(HTTPBadRequest):
            EncounterService.schedule_encounters(
                bad_dow, self.mock_admin_token, self.mock_breadcrumb
            )

    @patch("src.services.event_service.EventService.create_event")
    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_start_encounter_success(
        self, mock_get_mongo, mock_get_config, mock_get_profile, mock_create_event
    ):
        """Owning mentor starts scheduled encounter, decrements subscription balance, logs event."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}

        cust_sub = {"status": "active", "free_encounters_remaining": 5}
        customer_doc = {"_id": "cust-1", "subscriptions": [cust_sub]}
        mentee_profile = {
            "_id": self.VALID_MENTEE_ID,
            "customer_id": "cust-1",
            "display_name": "Bob Mentee",
        }
        mentor_profile = {
            "_id": self.VALID_MENTOR_ID,
            "display_name": "Jane Mentor",
        }
        encounter_doc = {
            "_id": "enc-1",
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "status": "scheduled",
        }

        mock_mongo = MagicMock()

        def mock_get_doc(coll, doc_id):
            if coll == "Customer" and str(doc_id) == "cust-1":
                return customer_doc
            if coll == "Profile" and str(doc_id) == self.VALID_MENTEE_ID:
                return mentee_profile
            if coll == "Profile" and str(doc_id) == self.VALID_MENTOR_ID:
                return mentor_profile
            if coll == "Encounter" and str(doc_id) == "enc-1":
                return encounter_doc
            return None

        mock_mongo.get_document.side_effect = mock_get_doc
        mock_mongo.update_document.return_value = {
            "_id": "enc-1",
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "status": "active",
        }
        mock_get_mongo.return_value = mock_mongo

        result = EncounterService.start_encounter(
            "enc-1", self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["mentor_name"], "Jane Mentor")
        self.assertEqual(result["mentee_name"], "Bob Mentee")

        # Verify customer subscription balance decremented
        self.assertEqual(cust_sub["free_encounters_remaining"], 4)
        mock_mongo.update_document.assert_any_call(
            "Customer",
            document_id="cust-1",
            set_data={"subscriptions": [cust_sub], "saved": self.mock_breadcrumb},
        )

        # Verify encounter status updated to active
        mock_mongo.update_document.assert_any_call(
            "Encounter",
            document_id="enc-1",
            set_data={"status": "active", "saved": self.mock_breadcrumb},
        )

        # Verify event logged
        mock_create_event.assert_called_once()
        event_arg = mock_create_event.call_args[0][0]
        self.assertEqual(event_arg["type"], "encounter")
        self.assertEqual(event_arg["context"]["encounter_id"], "enc-1")
        self.assertEqual(event_arg["context"]["mentor_id"], self.VALID_MENTOR_ID)
        self.assertEqual(event_arg["context"]["mentee_id"], self.VALID_MENTEE_ID)

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_start_encounter_insufficient_subscription_balance(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """Start encounter raises HTTPForbidden when customer has 0 remaining balance."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = lambda coll, doc_id: {
            ("Encounter", "enc-1"): {
                "_id": "enc-1",
                "mentor_id": self.VALID_MENTOR_ID,
                "mentee_id": self.VALID_MENTEE_ID,
                "status": "scheduled",
            },
            ("Profile", self.VALID_MENTEE_ID): {
                "_id": self.VALID_MENTEE_ID,
                "customer_id": "cust-1",
            },
            ("Customer", "cust-1"): {
                "_id": "cust-1",
                "subscriptions": [{"status": "active", "free_encounters_remaining": 0}],
            },
        }.get((coll, str(doc_id)))
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            EncounterService.start_encounter(
                "enc-1", self.mock_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_start_encounter_missing_customer(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """Start encounter raises HTTPForbidden when mentee profile has no customer."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = lambda coll, doc_id: {
            ("Encounter", "enc-1"): {
                "_id": "enc-1",
                "mentor_id": self.VALID_MENTOR_ID,
                "mentee_id": self.VALID_MENTEE_ID,
                "status": "scheduled",
            },
            ("Profile", self.VALID_MENTEE_ID): {
                "_id": self.VALID_MENTEE_ID,
                "customer_id": None,
            },
        }.get((coll, str(doc_id)))
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            EncounterService.start_encounter(
                "enc-1", self.mock_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_start_encounter_invalid_status(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """Start encounter raises HTTPForbidden if encounter is not 'scheduled'."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}

        mock_mongo = MagicMock()
        for invalid_status in ["active", "complete", "archived"]:
            mock_mongo.get_document.return_value = {
                "_id": "enc-1",
                "mentor_id": self.VALID_MENTOR_ID,
                "status": invalid_status,
            }
            mock_get_mongo.return_value = mock_mongo

            with self.assertRaises(HTTPForbidden):
                EncounterService.start_encounter(
                    "enc-1", self.mock_mentor_token, self.mock_breadcrumb
                )

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_start_encounter_forbidden_other_mentor(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """Non-owning mentor cannot start encounter."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": "other-mentor"}

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-1",
            "mentor_id": self.VALID_MENTOR_ID,
            "status": "scheduled",
        }
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            EncounterService.start_encounter(
                "enc-1", self.mock_other_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_start_encounter_not_found(self, mock_get_mongo, mock_get_config):
        """Start encounter raises HTTPNotFound if encounter does not exist."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            EncounterService.start_encounter(
                "missing-id", self.mock_admin_token, self.mock_breadcrumb
            )

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_finish_encounter_success(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """Owning mentor finishes active encounter."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = lambda coll, doc_id: {
            ("Encounter", "enc-1"): {
                "_id": "enc-1",
                "mentor_id": self.VALID_MENTOR_ID,
                "mentee_id": self.VALID_MENTEE_ID,
                "status": "active",
            },
            ("Profile", self.VALID_MENTOR_ID): {
                "_id": self.VALID_MENTOR_ID,
                "display_name": "Jane Mentor",
            },
            ("Profile", self.VALID_MENTEE_ID): {
                "_id": self.VALID_MENTEE_ID,
                "display_name": "Bob Mentee",
            },
        }.get((coll, str(doc_id)))

        mock_mongo.update_document.return_value = {
            "_id": "enc-1",
            "mentor_id": self.VALID_MENTOR_ID,
            "mentee_id": self.VALID_MENTEE_ID,
            "status": "complete",
        }
        mock_get_mongo.return_value = mock_mongo

        result = EncounterService.finish_encounter(
            "enc-1", self.mock_mentor_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["mentor_name"], "Jane Mentor")
        self.assertEqual(result["mentee_name"], "Bob Mentee")

        mock_mongo.update_document.assert_called_once_with(
            "Encounter",
            document_id="enc-1",
            set_data={"status": "complete", "saved": self.mock_breadcrumb},
        )

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_finish_encounter_invalid_status(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """Finish encounter raises HTTPForbidden if encounter is not 'active'."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": self.VALID_MENTOR_ID}

        mock_mongo = MagicMock()
        for invalid_status in ["scheduled", "complete", "archived"]:
            mock_mongo.get_document.return_value = {
                "_id": "enc-1",
                "mentor_id": self.VALID_MENTOR_ID,
                "status": invalid_status,
            }
            mock_get_mongo.return_value = mock_mongo

            with self.assertRaises(HTTPForbidden):
                EncounterService.finish_encounter(
                    "enc-1", self.mock_mentor_token, self.mock_breadcrumb
                )

    @patch("src.services.profile_service.ProfileService.get_profile_by_token")
    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_finish_encounter_forbidden_other_mentor(
        self, mock_get_mongo, mock_get_config, mock_get_profile
    ):
        """Non-owning mentor cannot finish encounter."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_get_profile.return_value = {"_id": "other-mentor"}

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "enc-1",
            "mentor_id": self.VALID_MENTOR_ID,
            "status": "active",
        }
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            EncounterService.finish_encounter(
                "enc-1", self.mock_other_mentor_token, self.mock_breadcrumb
            )

    @patch("src.services.encounter_service.Config.get_instance")
    @patch("src.services.encounter_service.MongoIO.get_instance")
    def test_finish_encounter_not_found(self, mock_get_mongo, mock_get_config):
        """Finish encounter raises HTTPNotFound if encounter does not exist."""
        mock_config = _make_config()
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            EncounterService.finish_encounter(
                "missing-id", self.mock_admin_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
