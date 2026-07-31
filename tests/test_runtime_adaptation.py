import unittest
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.learning.models import RuntimeLearningRecord
from omnilocal_runtime.learning.adaptation import RuntimeAdaptationEngine
from omnilocal_runtime.learning.manager import RuntimeLearningManager


class TestRuntimeAdaptation(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.learning_mgr = RuntimeLearningManager(db_manager=self.db)

    def test_calculate_learning_confidence(self):
        conf = RuntimeAdaptationEngine.calculate_learning_confidence(5, 10)
        self.assertGreaterEqual(conf, 0.50)
        self.assertLessEqual(conf, 0.99)

        conf_zero = RuntimeAdaptationEngine.calculate_learning_confidence(0, 0)
        self.assertEqual(conf_zero, 0.50)

    def test_generate_adaptation_for_failure_pattern(self):
        learning = RuntimeLearningRecord(
            id=1,
            learning_type="failure_pattern",
            pattern_detected="capability_binding",
            confidence=0.85
        )

        adaptation = RuntimeAdaptationEngine.generate_adaptation(learning)
        self.assertEqual(adaptation.target_area, "capability_binding")
        self.assertEqual(adaptation.priority, "high")
        self.assertEqual(adaptation.confidence, 0.85)

    def test_generate_adaptation_for_optimization(self):
        learning = RuntimeLearningRecord(
            id=2,
            learning_type="optimization",
            pattern_detected="high_runtime_stability",
            confidence=0.90
        )

        adaptation = RuntimeAdaptationEngine.generate_adaptation(learning)
        self.assertEqual(adaptation.target_area, "workflow_engine")
        self.assertEqual(adaptation.priority, "low")

    def test_evaluate_impact(self):
        learning = RuntimeLearningRecord(
            id=3,
            learning_type="failure_pattern",
            pattern_detected="memory_leak",
            confidence=0.80
        )
        adaptation = RuntimeAdaptationEngine.generate_adaptation(learning)
        impact = RuntimeAdaptationEngine.evaluate_impact(adaptation)

        self.assertIn("estimated_success_rate_increase_pct", impact)
        self.assertTrue(impact["requires_manual_approval"])

    def test_persist_adaptation_recommendation(self):
        rec = self.learning_mgr.generate_adaptation_recommendation(
            learning_id=10,
            target_area="validation",
            recommended_change="Aumentar timeout de validación a 10s",
            priority="medium",
            confidence=0.75,
            reasoning="Análisis de rendimiento muestra 3 reintentos exitosos."
        )

        self.assertIsNotNone(rec.id)
        self.assertEqual(rec.target_area, "validation")
        self.assertEqual(rec.priority, "medium")

        adaptations = self.learning_mgr.get_adaptations()
        self.assertTrue(any(a["id"] == rec.id for a in adaptations))


if __name__ == "__main__":
    unittest.main()
