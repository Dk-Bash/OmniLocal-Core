import os
import tempfile
import unittest
from database.sqlite_manager import SQLiteManager
from maintenance_strategy_evaluation.models import StrategyEvaluation
from maintenance_strategy_evaluation.manager import StrategyEvaluationManager
from maintenance_execution.manager import MaintenanceExecutionManager
from maintenance_decision.manager import MaintenanceDecisionManager


class TestExecutionPlanning(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db = SQLiteManager(db_path=self.db_path)
        self.db.create_tables()

        self.eval_manager = StrategyEvaluationManager(db_manager=self.db)
        self.decision_manager = MaintenanceDecisionManager(db_manager=self.db)
        self.execution_manager = MaintenanceExecutionManager(
            decision_manager=self.decision_manager
        )

    def tearDown(self):
        self.db.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_default_execution_plan(self):
        """Prueba que sin historial suficiente se genera un plan por defecto con risk_level='low' y requires_approval==False."""
        plan = self.execution_manager.create_execution_plan()

        self.assertIsNotNone(plan.id)
        self.assertEqual(plan.decision_type, "default")
        self.assertEqual(plan.risk_level, "low")
        self.assertEqual(plan.estimated_duration, "0m")
        self.assertFalse(plan.requires_approval)
        self.assertEqual(plan.requires_approval, False)
        self.assertTrue(len(plan.reasoning) > 0)
        self.assertEqual(
            plan.execution_steps,
            ["review_information", "wait_for_more_data"]
        )

    def test_adaptive_execution_plan(self):
        """Prueba que con historial adecuado la decisión es adaptativa y genera un plan con risk_level='medium', requires_approval==True y pasos completos."""
        eval_immediate = StrategyEvaluation(
            strategy_id="immediate_001",
            quality_score=1.0,
            impact_score=1.0,
            confidence_score=0.9,
            summary="Estrategia inmediata recomendada de alta confianza"
        )
        self.eval_manager.evaluate_strategy(eval_immediate)

        plan = self.execution_manager.create_execution_plan()

        self.assertIsNotNone(plan.id)
        self.assertEqual(plan.decision_type, "adaptive")
        self.assertEqual(plan.strategy_type, "immediate")
        self.assertEqual(plan.risk_level, "medium")
        self.assertEqual(plan.estimated_duration, "15m")
        self.assertTrue(plan.requires_approval)
        self.assertEqual(plan.requires_approval, True)
        self.assertTrue(len(plan.reasoning) > 0)
        self.assertEqual(
            plan.execution_steps,
            [
                "validate_strategy",
                "prepare_resources",
                "execute_controlled_maintenance",
                "record_result"
            ]
        )

    def test_sqlite_persistence(self):
        """Prueba que los planes de ejecución se guardan y recuperan de SQLite correctamente."""
        plan = self.execution_manager.create_execution_plan()

        retrieved = self.execution_manager.get_execution_plan(plan.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], plan.id)
        self.assertEqual(retrieved["decision_type"], plan.decision_type)
        self.assertEqual(retrieved["risk_level"], plan.risk_level)
        self.assertEqual(retrieved["requires_approval"], plan.requires_approval)
        self.assertEqual(retrieved["reasoning"], plan.reasoning)
        self.assertEqual(retrieved["execution_steps"], plan.execution_steps)

        all_plans = self.execution_manager.get_execution_plans()
        self.assertGreaterEqual(len(all_plans), 1)

    def test_integrity_no_side_effects(self):
        """Garantía de integridad: no modifica decisiones, ni estrategias, ni memorias, ni ejecuta acciones reales."""
        initial_eval_count = self.db.count_strategy_evaluations()
        initial_memory_count = self.db.count_memories()

        _ = self.execution_manager.create_execution_plan()

        self.assertEqual(self.db.count_strategy_evaluations(), initial_eval_count)
        self.assertEqual(self.db.count_memories(), initial_memory_count)


if __name__ == "__main__":
    unittest.main()
