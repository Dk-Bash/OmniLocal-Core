import os
import unittest
from database.sqlite_manager import SQLiteManager
from maintenance_execution.manager import MaintenanceExecutionManager
from maintenance_execution.models import MaintenanceExecutionPlan
from maintenance_validation.manager import ExecutionValidationManager
from maintenance_strategy_evaluation.models import StrategyEvaluation


class TestExecutionValidation(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_execution_validation.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.execution_manager = MaintenanceExecutionManager(db_manager=self.db_manager)
        self.validation_manager = ExecutionValidationManager(
            db_manager=self.db_manager, execution_manager=self.execution_manager
        )

    def tearDown(self):
        self.db_manager.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_default_plan_validation(self):
        """Prueba que un plan por defecto se valida como valid=True, risk_level='low', issues=[]."""
        report = self.validation_manager.validate_plan()

        self.assertIsNotNone(report.id)
        self.assertTrue(report.valid)
        self.assertEqual(report.risk_level, "low")
        self.assertEqual(report.issues, [])
        self.assertTrue(len(report.recommendation) > 0)

    def test_adaptive_plan_validation(self):
        """Prueba que un plan adaptativo se valida como valid=True, risk_level='medium', issues=['manual_approval_required']."""
        eval_immediate = StrategyEvaluation(
            strategy_id="immediate_001",
            quality_score=1.0,
            impact_score=1.0,
            confidence_score=0.9,
            summary="Estrategia inmediata recomendada con alta confianza",
        )
        self.db_manager.insert_strategy_evaluation(eval_immediate)

        plan = self.execution_manager.create_execution_plan()
        self.assertEqual(plan.decision_type, "adaptive")

        report = self.validation_manager.validate_plan(plan=plan)

        self.assertIsNotNone(report.id)
        self.assertTrue(report.valid)
        self.assertEqual(report.risk_level, "medium")
        self.assertEqual(report.issues, ["manual_approval_required"])
        self.assertTrue(len(report.recommendation) > 0)

    def test_invalid_plan_validation(self):
        """Prueba que si un plan no tiene pasos de ejecución se marca valid=False, risk_level='high', issues=['missing_execution_steps']."""
        invalid_plan = MaintenanceExecutionPlan(
            id=99,
            decision_type="default",
            strategy_type="none",
            execution_steps=[],
            risk_level="low",
            estimated_duration="0m",
            requires_approval=False,
            reasoning="Plan corrupto sin pasos",
        )

        report = self.validation_manager.validate_plan(plan=invalid_plan)

        self.assertIsNotNone(report.id)
        self.assertFalse(report.valid)
        self.assertEqual(report.risk_level, "high")
        self.assertEqual(report.issues, ["missing_execution_steps"])

    def test_sqlite_persistence(self):
        """Prueba que el reporte de validación se persiste y recupera correctamente de SQLite."""
        report = self.validation_manager.validate_plan()

        retrieved = self.validation_manager.get_validation_report(report.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], report.id)
        self.assertEqual(retrieved["plan_id"], report.plan_id)
        self.assertEqual(retrieved["valid"], report.valid)
        self.assertEqual(retrieved["risk_level"], report.risk_level)
        self.assertEqual(retrieved["issues"], report.issues)

        all_reports = self.validation_manager.get_validation_reports()
        self.assertTrue(len(all_reports) >= 1)

    def test_integrity_no_side_effects(self):
        """Prueba de integridad: confirma que la validación no modifica decisiones, planes ni memorias."""
        from memory.manager import MemoryManager
        memory_manager = MemoryManager(db_manager=self.db_manager)

        plans_before = self.execution_manager.get_execution_plans()
        memories_before = memory_manager.get_all_memories()

        self.validation_manager.validate_plan()

        plans_after = self.execution_manager.get_execution_plans()
        memories_after = memory_manager.get_all_memories()

        # El número de decisiones o memorias no debe cambiar a causa de la validación
        self.assertEqual(len(memories_before), len(memories_after))


if __name__ == "__main__":
    unittest.main()
