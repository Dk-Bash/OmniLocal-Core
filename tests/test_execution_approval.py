import os
import unittest
from database.sqlite_manager import SQLiteManager
from maintenance_execution.manager import MaintenanceExecutionManager
from maintenance_execution.models import MaintenanceExecutionPlan
from maintenance_validation.manager import ExecutionValidationManager
from maintenance_validation.models import ExecutionValidationReport
from maintenance_approval.manager import ExecutionApprovalManager
from maintenance_strategy_evaluation.models import StrategyEvaluation


class TestExecutionApproval(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_execution_approval.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.execution_manager = MaintenanceExecutionManager(db_manager=self.db_manager)
        self.validation_manager = ExecutionValidationManager(
            db_manager=self.db_manager, execution_manager=self.execution_manager
        )
        self.approval_manager = ExecutionApprovalManager(
            db_manager=self.db_manager, validation_manager=self.validation_manager
        )

    def tearDown(self):
        self.db_manager.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_low_risk_approval(self):
        """Prueba que un plan con validación correcta y bajo riesgo obtiene status 'approved' y approved=True."""
        approval = self.approval_manager.evaluate_approval()

        self.assertIsNotNone(approval.id)
        self.assertTrue(approval.approved)
        self.assertEqual(approval.approval_status, "approved")
        self.assertTrue("Aprobación" in approval.reason or "bajo" in approval.reason)

    def test_medium_risk_approval(self):
        """Prueba que un plan de riesgo medio obtiene status 'requires_review' y approved=False."""
        eval_immediate = StrategyEvaluation(
            strategy_id="immediate_001",
            quality_score=1.0,
            impact_score=1.0,
            confidence_score=0.9,
            summary="Estrategia inmediata recomendada",
        )
        self.db_manager.insert_strategy_evaluation(eval_immediate)

        plan = self.execution_manager.create_execution_plan()
        val_report = self.validation_manager.validate_plan(plan=plan)

        approval = self.approval_manager.evaluate_approval(validation_report=val_report)

        self.assertIsNotNone(approval.id)
        self.assertFalse(approval.approved)
        self.assertEqual(approval.approval_status, "requires_review")

    def test_invalid_validation_approval(self):
        """Prueba que una validación inválida genera estatus 'rejected' y approved=False."""
        invalid_plan = MaintenanceExecutionPlan(
            id=99,
            decision_type="default",
            strategy_type="none",
            execution_steps=[],
            risk_level="low",
            estimated_duration="0m",
            requires_approval=False,
            reasoning="Plan vacio sin pasos",
        )
        val_report = self.validation_manager.validate_plan(plan=invalid_plan)

        approval = self.approval_manager.evaluate_approval(validation_report=val_report)

        self.assertIsNotNone(approval.id)
        self.assertFalse(approval.approved)
        self.assertEqual(approval.approval_status, "rejected")

    def test_sqlite_persistence(self):
        """Prueba que la aprobación se persiste y recupera correctamente de la base de datos SQLite."""
        approval = self.approval_manager.evaluate_approval()

        retrieved = self.approval_manager.get_execution_approval(approval.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], approval.id)
        self.assertEqual(retrieved["plan_id"], approval.plan_id)
        self.assertEqual(retrieved["validation_id"], approval.validation_id)
        self.assertEqual(retrieved["approval_status"], approval.approval_status)
        self.assertEqual(retrieved["approved"], approval.approved)
        self.assertEqual(retrieved["reason"], approval.reason)

        all_approvals = self.approval_manager.get_execution_approvals()
        self.assertTrue(len(all_approvals) >= 1)

    def test_integrity_no_side_effects(self):
        """Prueba de integridad: confirma que la evaluación de aprobación no modifica planes, validaciones ni memorias."""
        from memory.manager import MemoryManager
        memory_manager = MemoryManager(db_manager=self.db_manager)

        val_report = self.validation_manager.validate_plan()

        plans_before = self.execution_manager.get_execution_plans()
        validations_before = self.validation_manager.get_validation_reports()
        memories_before = memory_manager.get_all_memories()

        self.approval_manager.evaluate_approval(validation_report=val_report)

        plans_after = self.execution_manager.get_execution_plans()
        validations_after = self.validation_manager.get_validation_reports()
        memories_after = memory_manager.get_all_memories()

        self.assertEqual(len(plans_before), len(plans_after))
        self.assertEqual(len(validations_before), len(validations_after))
        self.assertEqual(len(memories_before), len(memories_after))


if __name__ == "__main__":
    unittest.main()
