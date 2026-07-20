"""
Unit tests for Plan service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from pymongo import ASCENDING
from src.services.plan_service import PlanService
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestPlanService(unittest.TestCase):
    """Test cases for PlanService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_create_plan_success(self, mock_get_mongo, mock_get_config):
        """Test successful creation of a plan document."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {
            "name": "test-plan",
            "description": "Test plan",
            "status": "active",
        }

        plan_id = PlanService.create_plan(data, self.mock_token, self.mock_breadcrumb)

        self.assertEqual(plan_id, "123")
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Plan")
        created_data = call_args[0][1]
        self.assertIn("created", created_data)
        self.assertIn("saved", created_data)
        self.assertEqual(created_data["name"], "test-plan")

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_create_plan_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "name": "test"}

        PlanService.create_plan(data, self.mock_token, self.mock_breadcrumb)

        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_get_plans_returns_all_sorted_by_name(
        self, mock_get_mongo, mock_get_config
    ):
        """get_plans returns a page (default name asc) as a plain list."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        plans = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "alpha"},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "beta"},
        ]
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = plans
        mock_get_mongo.return_value = mock_mongo

        result = PlanService.get_plans(self.mock_token, self.mock_breadcrumb)

        self.assertEqual(result, plans)
        mock_mongo.get_documents.assert_called_once()
        args, kwargs = mock_mongo.get_documents.call_args
        self.assertEqual(args[0], "Plan")
        # Default order is name asc with a stable _id tiebreaker; default page.
        self.assertEqual(kwargs["sort_by"], [("name", ASCENDING), ("_id", ASCENDING)])
        self.assertEqual(kwargs["skip"], 0)
        self.assertEqual(kwargs["limit"], 20)

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_get_plans_applies_pagination_and_name_filter(
        self, mock_get_mongo, mock_get_config
    ):
        """get_plans honors offset/size and the optional name contains filter."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        PlanService.get_plans(
            self.mock_token,
            self.mock_breadcrumb,
            offset=10,
            size=5,
            filters={"name": "intro"},
            sort_by=[("name", ASCENDING), ("_id", ASCENDING)],
        )

        args, kwargs = mock_mongo.get_documents.call_args
        self.assertEqual(args[0], "Plan")
        self.assertEqual(
            kwargs["match"], {"name": {"$regex": "intro", "$options": "i"}}
        )
        self.assertEqual(kwargs["skip"], 10)
        self.assertEqual(kwargs["limit"], 5)

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_get_plan_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific plan document."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "plan1",
        }
        mock_get_mongo.return_value = mock_mongo

        result = PlanService.get_plan("123", self.mock_token, self.mock_breadcrumb)

        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Plan", "123")

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_get_plan_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_plan raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            PlanService.get_plan("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_update_plan_success(self, mock_get_mongo, mock_get_config):
        """Test successful update of a plan document."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": "123",
            "name": "updated-plan",
        }
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "updated-plan", "description": "Updated"}

        updated = PlanService.update_plan(
            "123", data, self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "updated-plan")
        mock_mongo.update_document.assert_called_once()
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[1]["document_id"], "123")
        set_data = call_args[1]["set_data"]
        self.assertIn("saved", set_data)
        self.assertEqual(set_data["name"], "updated-plan")

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_update_plan_prevent_restricted_fields(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_plan raises HTTPForbidden for restricted fields."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "999", "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PlanService.update_plan("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("_id", str(context.exception))

        data = {"created": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PlanService.update_plan("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("created", str(context.exception))

        data = {"saved": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            PlanService.update_plan("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("saved", str(context.exception))

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_update_plan_not_found(self, mock_get_mongo, mock_get_config):
        """Test update_plan raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            PlanService.update_plan(
                "999", {"name": "Updated"}, self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_update_plan_uses_breadcrumb_directly(
        self, mock_get_mongo, mock_get_config
    ):
        """Test update_plan uses breadcrumb directly for saved field."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
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

        result = PlanService.update_plan(
            "123", {"name": "updated"}, self.mock_token, breadcrumb
        )

        self.assertIsNotNone(result)
        call_args = mock_mongo.update_document.call_args
        set_data = call_args[1]["set_data"]
        self.assertEqual(set_data["saved"], breadcrumb)
        self.assertEqual(set_data["saved"]["from_ip"], "192.168.1.1")

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_create_plan_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test create_plan handles database exceptions."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PlanService.create_plan(
                {"name": "test"}, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_get_plans_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_plans handles database exceptions."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PlanService.get_plans(self.mock_token, self.mock_breadcrumb)

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_get_plan_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_plan handles database exceptions."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PlanService.get_plan("123", self.mock_token, self.mock_breadcrumb)

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_update_plan_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test update_plan handles database exceptions."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PlanService.update_plan(
                "123", {"name": "updated"}, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_create_plan_persists_checklist(self, mock_get_mongo, mock_get_config):
        """`checklist` is passed through to storage unchanged."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"name": "test-plan", "checklist": ["step one", "step two"]}
        PlanService.create_plan(data, self.mock_token, self.mock_breadcrumb)

        created_data = mock_mongo.create_document.call_args[0][1]
        self.assertEqual(created_data["checklist"], ["step one", "step two"])

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_update_plan_persists_checklist(self, mock_get_mongo, mock_get_config):
        """`checklist` is passed through to set_data and returned unchanged."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {"_id": "123", "checklist": ["a"]}
        mock_get_mongo.return_value = mock_mongo

        updated = PlanService.update_plan(
            "123", {"checklist": ["a"]}, self.mock_token, self.mock_breadcrumb
        )

        set_data = mock_mongo.update_document.call_args[1]["set_data"]
        self.assertEqual(set_data["checklist"], ["a"])
        self.assertEqual(updated["checklist"], ["a"])

    @patch("src.services.plan_service.Config.get_instance")
    @patch("src.services.plan_service.MongoIO.get_instance")
    def test_get_plan_returns_checklist(self, mock_get_mongo, mock_get_config):
        """get_plan returns the stored `checklist` unchanged."""
        mock_config = MagicMock()
        mock_config.PLAN_COLLECTION_NAME = "Plan"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "plan1",
            "checklist": ["do x", "do y"],
        }
        mock_get_mongo.return_value = mock_mongo

        result = PlanService.get_plan("123", self.mock_token, self.mock_breadcrumb)

        self.assertEqual(result["checklist"], ["do x", "do y"])


if __name__ == "__main__":
    unittest.main()
