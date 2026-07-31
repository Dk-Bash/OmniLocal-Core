import unittest
import tempfile
import os
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.context import RuntimeContext
from omnilocal_runtime.models import RuntimeResult
from omnilocal_runtime.engine import OmniLocalEngine


class TestRuntimeEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_engine.db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

    def tearDown(self):
        self.db_manager.close()
        self.temp_dir.cleanup()

    def test_context_validation(self):
        ctx = RuntimeContext(operation_type="memory_optimization")
        self.assertEqual(ctx.status, "initialized")
        self.assertEqual(ctx.current_stage, "init")
        self.assertEqual(ctx.metadata, {})

        with self.assertRaises(ValueError):
            RuntimeContext(operation_type="test", status="invalid_status")

    def test_engine_create_context(self):
        engine = OmniLocalEngine(db_manager=self.db_manager)
        ctx = engine.create_context("memory_optimization", metadata={"env": "test"})

        self.assertIsNotNone(ctx.id)
        self.assertEqual(ctx.operation_type, "memory_optimization")
        self.assertEqual(ctx.status, "initialized")
        self.assertEqual(ctx.metadata, {"env": "test"})

        db_ctx = self.db_manager.get_runtime_context(ctx.id)
        self.assertIsNotNone(db_ctx)
        self.assertEqual(db_ctx["operation_type"], "memory_optimization")
        self.assertEqual(db_ctx["status"], "initialized")

    def test_engine_run_default_memory_optimization_pipeline(self):
        engine = OmniLocalEngine(db_manager=self.db_manager)
        ctx = engine.create_context("memory_optimization")

        result = engine.run_pipeline(ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.context_id, ctx.id)
        self.assertEqual(len(result.executed_stages), 8)
        self.assertEqual(ctx.status, "completed")
        self.assertEqual(ctx.current_stage, "learning_feedback")

        # Verificar las 8 etapas del pipeline de optimización de memoria
        stage_names = [s["name"] for s in result.executed_stages]
        expected_stages = [
            "memory_analysis",
            "priority_evaluation",
            "simulation",
            "governance_check",
            "decision",
            "execution_planning",
            "result_tracking",
            "learning_feedback",
        ]
        self.assertEqual(stage_names, expected_stages)

    def test_engine_dependency_injection_no_side_effects(self):
        class MockManager:
            pass

        mock_mem = MockManager()
        mock_dec = MockManager()
        mock_exec = MockManager()

        engine = OmniLocalEngine(
            memory_manager=mock_mem,
            decision_manager=mock_dec,
            execution_manager=mock_exec,
            db_manager=self.db_manager,
        )

        ctx = engine.create_context("custom_orchestration")
        result = engine.run_pipeline(ctx)

        self.assertTrue(result.success)
        self.assertIs(engine.memory_manager, mock_mem)
        self.assertIs(engine.decision_manager, mock_dec)
        self.assertIs(engine.execution_manager, mock_exec)


if __name__ == "__main__":
    unittest.main()
