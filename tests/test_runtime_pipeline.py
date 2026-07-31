import unittest
import tempfile
import os
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.context import RuntimeContext
from omnilocal_runtime.models import RuntimeResult
from omnilocal_runtime.pipeline import RuntimePipeline


class TestRuntimePipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_pipeline.db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

    def tearDown(self):
        self.db_manager.close()
        self.temp_dir.cleanup()

    def test_pipeline_add_stage_and_status(self):
        pipeline = RuntimePipeline(name="test_pipe")
        pipeline.add_stage("stage_1").add_stage("stage_2")

        status_list = pipeline.get_status()
        self.assertEqual(len(status_list), 2)
        self.assertEqual(status_list[0], {"name": "stage_1", "status": "pending"})
        self.assertEqual(status_list[1], {"name": "stage_2", "status": "pending"})

    def test_pipeline_successful_execution(self):
        context = RuntimeContext(operation_type="unit_test")
        ctx_id = self.db_manager.insert_runtime_context(
            context.operation_type, context.status, context.current_stage
        )
        context.id = ctx_id

        executed_stages = []

        def handler_1(ctx):
            executed_stages.append("stage_1")

        def handler_2(ctx):
            executed_stages.append("stage_2")

        pipeline = RuntimePipeline(name="success_pipe")
        pipeline.add_stage("stage_1", handler_1).add_stage("stage_2", handler_2)

        result = pipeline.execute(context, db_manager=self.db_manager)

        self.assertTrue(result.success)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(context.status, "completed")
        self.assertEqual(context.current_stage, "stage_2")
        self.assertEqual(executed_stages, ["stage_1", "stage_2"])

        # Verificar persistencia en DB
        db_ctx = self.db_manager.get_runtime_context(ctx_id)
        self.assertEqual(db_ctx["status"], "completed")
        self.assertEqual(db_ctx["current_stage"], "stage_2")

    def test_pipeline_failure_and_skipping(self):
        context = RuntimeContext(operation_type="unit_test_failure")
        ctx_id = self.db_manager.insert_runtime_context(
            context.operation_type, context.status, context.current_stage
        )
        context.id = ctx_id

        def failing_handler(ctx):
            raise ValueError("Simulated stage error")

        pipeline = RuntimePipeline(name="failing_pipe")
        pipeline.add_stage("stage_pass", lambda ctx: None)
        pipeline.add_stage("stage_fail", failing_handler)
        pipeline.add_stage("stage_skip", lambda ctx: None)

        result = pipeline.execute(context, db_manager=self.db_manager)

        self.assertFalse(result.success)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Simulated stage error", result.errors[0])
        self.assertEqual(context.status, "failed")
        self.assertEqual(context.current_stage, "stage_fail")

        statuses = pipeline.get_status()
        self.assertEqual(statuses[0], {"name": "stage_pass", "status": "completed"})
        self.assertEqual(statuses[1], {"name": "stage_fail", "status": "failed"})
        self.assertEqual(statuses[2], {"name": "stage_skip", "status": "skipped"})


if __name__ == "__main__":
    unittest.main()
