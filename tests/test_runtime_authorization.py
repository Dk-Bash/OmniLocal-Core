import unittest
import os
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.planning.manager import RuntimePlanningManager
from omnilocal_runtime.plan_validation.manager import RuntimePlanValidationManager
from omnilocal_runtime.authorization.manager import RuntimeAuthorizationManager
from omnilocal_runtime.authorization.evaluator import RuntimeAuthorizationEvaluator


class TestRuntimeAuthorization(unittest.TestCase):

    def setUp(self):
        self.db_path = "data/test_auth.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.planning_mgr = RuntimePlanningManager(db_manager=self.db_manager)
        self.validation_mgr = RuntimePlanValidationManager(db_manager=self.db_manager, planning_manager=self.planning_mgr)
        self.auth_mgr = RuntimeAuthorizationManager(db_manager=self.db_manager, validation_manager=self.validation_mgr)

    def tearDown(self):
        self.db_manager.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_authorize_approved_plan(self):
        plan = self.planning_mgr.create_plan()
        val_report = self.validation_mgr.validate(plan_id=plan.id)

        auth = self.auth_mgr.authorize_plan(plan_id=plan.id, validation_id=val_report.id)
        self.assertIn(auth.authorization_status, ["authorized", "authorized_with_conditions"])
        self.assertGreater(auth.id, 0)
        self.assertGreater(len(auth.conditions), 0)

    def test_authorize_rejected_plan(self):
        plan = self.planning_mgr.create_plan()
        val_report_dict = {
            "id": 999,
            "plan_id": plan.id,
            "validation_status": "rejected",
            "risk_level": "critical",
            "checks_performed": ["safety_check"],
            "failed_checks": ["critical_security_failure"],
            "recommendation": "Reject plan"
        }

        auth = RuntimeAuthorizationEvaluator.evaluate_authorization(
            validation_report=val_report_dict,
            plan_id=plan.id,
            validation_id=999
        )
        self.assertEqual(auth.authorization_status, "rejected")
        self.assertEqual(auth.authorization_level, "blocked")

    def test_persistence_and_retrieval(self):
        plan = self.planning_mgr.create_plan()
        auth = self.auth_mgr.authorize_plan(plan_id=plan.id)

        retrieved = self.auth_mgr.get_authorization(auth.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, auth.id)
        self.assertEqual(retrieved.authorization_status, auth.authorization_status)
        self.assertEqual(len(retrieved.conditions), len(auth.conditions))

        all_auths = self.auth_mgr.get_authorizations()
        self.assertGreaterEqual(len(all_auths), 1)

    def test_invariance_rules(self):
        plan = self.planning_mgr.create_plan()
        plan_before = plan.to_dict()

        val_report = self.validation_mgr.validate(plan_id=plan.id)
        val_before = val_report.to_dict()

        # Authorize plan
        auth = self.auth_mgr.authorize_plan(plan_id=plan.id, validation_id=val_report.id)

        # Confirm original plan is not modified
        plan_after = self.planning_mgr.get_plan(plan.id)
        self.assertEqual(plan_before["plan_type"], plan_after["plan_type"])
        self.assertEqual(plan_before["steps"], plan_after["steps"])

        # Confirm validation report is not modified
        val_after_rows = self.db_manager.get_plan_validations()
        val_after = next((v for v in val_after_rows if v["id"] == val_report.id), None)
        self.assertEqual(val_before["validation_status"], val_after["validation_status"])


if __name__ == "__main__":
    unittest.main()
