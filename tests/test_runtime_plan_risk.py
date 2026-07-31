import unittest
from omnilocal_runtime.planning.models import RuntimePlanStep
from omnilocal_runtime.planning.risk import RuntimeRiskEvaluator
from omnilocal_runtime.planning.planner import RuntimePlannerEngine


class TestRuntimePlanRisk(unittest.TestCase):

    def test_calculate_risk_score(self):
        score = RuntimeRiskEvaluator.calculate_risk_score(
            step_count=3,
            complexity=1.5,
            failure_history_count=2,
            decision_confidence=0.8
        )
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_evaluate_plan_risk_levels(self):
        low_steps = [RuntimePlanStep(step_number=1, risk_level="low")]
        low_risk = RuntimeRiskEvaluator.evaluate_plan_risk(steps=low_steps, complexity=0.5, decision_confidence=0.95)
        self.assertIn(low_risk, ["low", "medium"])

        critical_steps = [RuntimePlanStep(step_number=1, risk_level="critical")]
        critical_risk = RuntimeRiskEvaluator.evaluate_plan_risk(steps=critical_steps, complexity=1.0)
        self.assertEqual(critical_risk, "critical")

    def test_generate_risk_summary(self):
        summary = RuntimeRiskEvaluator.generate_risk_summary("high", 0.65, 4)
        self.assertIn("HIGH", summary)
        self.assertIn("0.65", summary)
        self.assertIn("4 pasos", summary)

    def test_planner_complexity_and_steps(self):
        steps = RuntimePlannerEngine.generate_steps("fallback")
        self.assertEqual(len(steps), 3)

        complexity = RuntimePlannerEngine.estimate_complexity(steps, "fallback")
        self.assertGreaterEqual(complexity, 2.0)

        plan = RuntimePlannerEngine.generate_plan({"id": 1, "decision_type": "fallback", "confidence": 0.85})
        self.assertEqual(plan.plan_type, "fallback_plan")
        self.assertIn(plan.estimated_risk, ["medium", "high", "critical"])


if __name__ == "__main__":
    unittest.main()
