import unittest
import json
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.planning.manager import RuntimePlanningManager
from omnilocal_runtime.plan_validation.validator import RuntimePlanValidator
from omnilocal_runtime.plan_validation.manager import RuntimePlanValidationManager


class TestPlanValidation(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.planning_mgr = RuntimePlanningManager(db_manager=self.db)
        self.validation_mgr = RuntimePlanValidationManager(
            db_manager=self.db,
            planning_manager=self.planning_mgr
        )

    def test_validator_approval_flow(self):
        sample_plan = {
            "id": 100,
            "plan_type": "optimization_plan",
            "estimated_risk": "low",
            "confidence": 0.85,
            "steps": json.dumps([{"step_number": 1, "description": "Optimize queries"}])
        }
        sample_sim = {
            "simulation_status": "success",
            "confidence": 0.80
        }

        report = RuntimePlanValidator.validate_plan(sample_plan, sample_sim)
        self.assertEqual(report.plan_id, 100)
        self.assertEqual(report.validation_status, "approved")
        self.assertIn("APROBADO", report.recommendation)

    def test_validator_rejection_flow(self):
        sample_plan = {
            "id": 101,
            "plan_type": "fallback_plan",
            "estimated_risk": "critical",
            "confidence": 0.35,
            "steps": json.dumps([{"step_number": 1, "description": "Reset database"}])
        }
        sample_sim = {
            "simulation_status": "failure",
            "confidence": 0.20
        }

        report = RuntimePlanValidator.validate_plan(sample_plan, sample_sim)
        self.assertEqual(report.validation_status, "rejected")
        self.assertIn("RECHAZADO", report.recommendation)

    def test_full_validate_manager_flow(self):
        plan = self.planning_mgr.create_plan(current_metrics={"error_rate": 0.05, "avg_latency": 280})
        report = self.validation_mgr.validate(plan_id=plan.id)

        self.assertIsNotNone(report.id)
        self.assertEqual(report.plan_id, plan.id)
        self.assertIn(report.validation_status, ["approved", "approved_with_warnings", "rejected"])

        fetched = self.validation_mgr.get_validation_report(report.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], report.id)
        self.assertEqual(fetched["validation_status"], report.validation_status)

        all_reports = self.validation_mgr.get_validation_reports()
        self.assertTrue(any(r["id"] == report.id for r in all_reports))

    def test_invariance_rules(self):
        plans_before = len(self.planning_mgr.get_plans())
        decisions_before = len(self.planning_mgr.decision_manager.get_decisions())
        knowledge_before = len(self.planning_mgr.knowledge_manager.get_knowledge_entries())

        # Validar plan
        plan = self.planning_mgr.create_plan(current_metrics={"error_rate": 0.0, "avg_latency": 100})
        self.validation_mgr.validate(plan_id=plan.id)

        plans_after = len(self.planning_mgr.get_plans())
        decisions_after = len(self.planning_mgr.decision_manager.get_decisions())
        knowledge_after = len(self.planning_mgr.knowledge_manager.get_knowledge_entries())

        # No se borró ni modificó información previa
        self.assertGreaterEqual(plans_after, plans_before)
        self.assertEqual(decisions_after, decisions_before + 1)  # La creación del plan usó 1 decisión
        self.assertEqual(knowledge_after, knowledge_before)


if __name__ == "__main__":
    unittest.main()
