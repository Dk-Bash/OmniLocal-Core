import unittest
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.learning.manager import RuntimeLearningManager
from omnilocal_runtime.learning.patterns import RuntimePatternAnalyzer
from omnilocal_runtime.validation.manager import RuntimeValidationManager


class TestRuntimeLearning(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.val_mgr = RuntimeValidationManager(db_manager=self.db)
        self.learning_mgr = RuntimeLearningManager(db_manager=self.db, val_manager=self.val_mgr)

    def test_generate_learning_record(self):
        record = self.learning_mgr.generate_learning_record(
            learning_type="failure_pattern",
            pattern_detected="validation_timeout",
            source_execution_id=1,
            confidence=0.88,
            impact_prediction="Reducción de latencia y prevención de timeouts"
        )
        self.assertIsNotNone(record.id)
        self.assertEqual(record.learning_type, "failure_pattern")
        self.assertEqual(record.pattern_detected, "validation_timeout")
        self.assertEqual(record.confidence, 0.88)

        records = self.learning_mgr.get_learning_records()
        self.assertTrue(any(r["id"] == record.id for r in records))

    def test_analyze_execution_history(self):
        # Generar ejecuciones de prueba en la capa de validación
        self.val_mgr.execute_scenario("memory_optimization_success")
        self.val_mgr.execute_scenario("capability_failure_handling")

        analysis = self.learning_mgr.analyze_execution_history()
        self.assertIn("total_executions_analyzed", analysis)
        self.assertIn("learnings_generated", analysis)
        self.assertIn("adaptations_generated", analysis)
        self.assertGreaterEqual(len(analysis["learnings_generated"]), 1)
        self.assertGreaterEqual(len(analysis["adaptations_generated"]), 1)

    def test_pattern_analyzer_failure_and_success(self):
        sample_data = [
            {"status": "failed", "failed_stage": "memory_binding"},
            {"status": "failed", "failed_stage": "memory_binding"},
            {"status": "passed"},
            {"status": "completed"}
        ]

        failures = RuntimePatternAnalyzer.detect_failure_patterns(sample_data)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["target_area"], "memory_binding")
        self.assertEqual(failures[0]["occurrences"], 2)

        successes = RuntimePatternAnalyzer.detect_success_patterns(sample_data)
        self.assertEqual(len(successes), 1)
        self.assertEqual(successes[0]["successful_executions"], 2)

    def test_historical_records_unmodified(self):
        # Verificar que la ejecución del análisis de aprendizaje no modifica ni borra reportes históricos
        val_before = len(self.val_mgr.get_reports())
        self.learning_mgr.analyze_execution_history()
        val_after = len(self.val_mgr.get_reports())
        self.assertEqual(val_before, val_after)


if __name__ == "__main__":
    unittest.main()
