import unittest
import tempfile
import os
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.engine import OmniLocalEngine
from omnilocal_runtime.workflows.engine import WorkflowEngine
from omnilocal_runtime.workflows.memory_optimization import MemoryOptimizationWorkflow


class TestMemoryOptimizationWorkflow(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_mem_opt.db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.core_engine = OmniLocalEngine(db_manager=self.db_manager)
        self.wf_engine = WorkflowEngine(engine=self.core_engine, db_manager=self.db_manager)

    def tearDown(self):
        self.db_manager.close()
        self.temp_dir.cleanup()

    def test_memory_optimization_definition_stages(self):
        mem_wf = MemoryOptimizationWorkflow()
        wf_def = mem_wf.get_definition()

        expected_stages = [
            "memory_analysis",
            "priority_evaluation",
            "simulation",
            "governance_check",
            "decision_generation",
            "execution_planning",
            "validation",
            "feedback_generation",
            "learning_update",
        ]

        self.assertEqual(wf_def.name, "memory_optimization")
        self.assertEqual(len(wf_def.stages), 9)
        self.assertEqual(wf_def.stages, expected_stages)

    def test_stage_output_structure(self):
        mem_wf = MemoryOptimizationWorkflow()
        result = mem_wf.run_stage("memory_analysis")

        self.assertIn("stage_name", result)
        self.assertIn("status", result)
        self.assertIn("summary", result)
        self.assertEqual(result["stage_name"], "memory_analysis")
        self.assertEqual(result["status"], "completed")

    def test_full_execution_order_and_integrity(self):
        execution = self.wf_engine.execute_workflow("memory_optimization")

        self.assertEqual(execution.status, "completed")
        self.assertEqual(execution.current_stage, "learning_update")
        self.assertEqual(len(execution.results), 9)

        expected_stages = [
            "memory_analysis",
            "priority_evaluation",
            "simulation",
            "governance_check",
            "decision_generation",
            "execution_planning",
            "validation",
            "feedback_generation",
            "learning_update",
        ]

        executed_names = [stage_res["stage_name"] for stage_res in execution.results]
        self.assertEqual(executed_names, expected_stages)

        for res in execution.results:
            self.assertEqual(res["status"], "completed")
            self.assertIsNotNone(res["summary"])
            self.assertTrue(len(res["summary"]) > 0)

    def test_read_only_integrity_guarantee(self):
        # Asegurar que la ejecución no altere las tablas de memorias existentes
        initial_memories = self.db_manager.get_all_memories_for_audit()
        self.wf_engine.execute_workflow("memory_optimization")
        post_memories = self.db_manager.get_all_memories_for_audit()

        self.assertEqual(len(initial_memories), len(post_memories))


if __name__ == "__main__":
    unittest.main()
