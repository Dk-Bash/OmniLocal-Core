import unittest
import tempfile
import os
import json
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.engine import OmniLocalEngine
from omnilocal_runtime.workflows.models import WorkflowDefinition, WorkflowExecution
from omnilocal_runtime.workflows.engine import WorkflowEngine


class TestWorkflowEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_workflow_engine.db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.core_engine = OmniLocalEngine(db_manager=self.db_manager)
        self.wf_engine = WorkflowEngine(engine=self.core_engine, db_manager=self.db_manager)

    def tearDown(self):
        self.db_manager.close()
        self.temp_dir.cleanup()

    def test_register_workflow(self):
        wf_def = WorkflowDefinition(
            name="custom_test_workflow",
            description="Workflow de prueba personalizado",
            stages=["stage_a", "stage_b"],
        )
        registered = self.wf_engine.register_workflow(wf_def)
        self.assertEqual(registered.name, "custom_test_workflow")
        self.assertIn("custom_test_workflow", self.wf_engine.registry)

    def test_execute_workflow_and_get_execution(self):
        wf_def = WorkflowDefinition(
            name="simple_pipeline",
            description="Pipeline simple de verificación",
            stages=["init_check", "process_check"],
        )
        self.wf_engine.register_workflow(wf_def)

        execution = self.wf_engine.execute_workflow("simple_pipeline", metadata={"test": "ok"})

        self.assertIsNotNone(execution.id)
        self.assertEqual(execution.workflow_id, "simple_pipeline")
        self.assertEqual(execution.status, "completed")
        self.assertEqual(len(execution.results), 2)
        self.assertEqual(execution.results[0]["stage_name"], "init_check")
        self.assertEqual(execution.results[1]["stage_name"], "process_check")

        # Verificar recuperación desde DB
        fetched = self.wf_engine.get_execution(execution.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, execution.id)
        self.assertEqual(fetched.workflow_id, "simple_pipeline")
        self.assertEqual(fetched.status, "completed")
        self.assertEqual(len(fetched.results), 2)

    def test_execute_unregistered_workflow_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.wf_engine.execute_workflow("non_existent_workflow")

    def test_dependency_injection_integrity(self):
        self.assertIs(self.wf_engine.engine, self.core_engine)
        self.assertIs(self.wf_engine.db_manager, self.db_manager)


if __name__ == "__main__":
    unittest.main()
