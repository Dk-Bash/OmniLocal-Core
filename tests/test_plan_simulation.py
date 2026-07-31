import unittest
import json
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.planning.manager import RuntimePlanningManager
from omnilocal_runtime.plan_validation.simulator import RuntimePlanSimulator
from omnilocal_runtime.plan_validation.manager import RuntimePlanValidationManager


class TestPlanSimulation(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.planning_mgr = RuntimePlanningManager(db_manager=self.db)
        self.validation_mgr = RuntimePlanValidationManager(
            db_manager=self.db,
            planning_manager=self.planning_mgr
        )

    def test_simulator_unit_outcomes(self):
        sample_plan = {
            "id": 10,
            "plan_type": "optimization_plan",
            "estimated_risk": "low",
            "confidence": 0.85,
            "steps": json.dumps([{"step_number": 1, "description": "Adjust thread pool"}])
        }

        sim_res = RuntimePlanSimulator.simulate_plan(sample_plan)
        self.assertEqual(sim_res.plan_id, 10)
        self.assertEqual(sim_res.simulation_status, "success")
        self.assertGreater(sim_res.confidence, 0.70)
        self.assertIn("Optimización", sim_res.predicted_outcome)

    def test_simulator_critical_risk_failure(self):
        sample_plan = {
            "id": 11,
            "plan_type": "fallback_plan",
            "estimated_risk": "critical",
            "confidence": 0.30,
            "steps": json.dumps([{"step_number": 1, "description": "Purge memory"}])
        }

        sim_res = RuntimePlanSimulator.simulate_plan(sample_plan)
        self.assertEqual(sim_res.simulation_status, "failure")
        self.assertLess(sim_res.confidence, 0.50)
        self.assertIn("Riesgo elevado", sim_res.predicted_issues)

    def test_simulate_flow_and_persistence(self):
        plan = self.planning_mgr.create_plan(current_metrics={"error_rate": 0.02, "avg_latency": 150})
        sim_res = self.validation_mgr.simulate(plan_id=plan.id)

        self.assertIsNotNone(sim_res.id)
        self.assertEqual(sim_res.plan_id, plan.id)
        self.assertIn(sim_res.simulation_status, ["success", "partial", "failure"])

        fetched = self.validation_mgr.get_simulation_result(sim_res.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], sim_res.id)
        self.assertEqual(fetched["plan_id"], plan.id)

        all_sims = self.validation_mgr.get_simulation_results()
        self.assertTrue(any(s["id"] == sim_res.id for s in all_sims))

    def test_invariance_plan_not_modified(self):
        plan = self.planning_mgr.create_plan(current_metrics={"error_rate": 0.0, "avg_latency": 100})
        plan_before = self.planning_mgr.get_plan(plan.id)

        # Simular
        self.validation_mgr.simulate(plan_id=plan.id)

        plan_after = self.planning_mgr.get_plan(plan.id)

        # El plan original no fue modificado en absoluto
        self.assertEqual(plan_before["plan_type"], plan_after["plan_type"])
        self.assertEqual(plan_before["steps"], plan_after["steps"])
        self.assertEqual(plan_before["estimated_risk"], plan_after["estimated_risk"])
        self.assertEqual(plan_before["confidence"], plan_after["confidence"])


if __name__ == "__main__":
    unittest.main()
