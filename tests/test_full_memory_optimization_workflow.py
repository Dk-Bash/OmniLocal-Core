import unittest
import tempfile
import os
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.engine import OmniLocalEngine
from omnilocal_runtime.workflows.engine import WorkflowEngine
from omnilocal_runtime.bindings.manager import CapabilityBindingManager
from omnilocal_runtime.bindings.memory_binding import MemoryCapabilityBinding
from omnilocal_runtime.workflows.memory_optimization import STAGES_LIST


class TestFullMemoryOptimizationWorkflow(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_full_memory_workflow.db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

        self.core_engine = OmniLocalEngine(db_manager=self.db_manager)
        self.binding_manager = CapabilityBindingManager(db_manager=self.db_manager)
        self.mem_binding = MemoryCapabilityBinding(db_manager=self.db_manager)
        self.mem_binding.register_all(self.binding_manager)

        self.wf_engine = WorkflowEngine(
            engine=self.core_engine,
            capability_binding_manager=self.binding_manager,
            db_manager=self.db_manager,
        )

    def tearDown(self):
        self.db_manager.close()
        self.temp_dir.cleanup()

    def test_full_workflow_executes_all_9_stages_in_order(self):
        execution = self.wf_engine.execute_workflow("memory_optimization")

        self.assertEqual(execution.status, "completed")
        self.assertEqual(len(execution.results), 9)

        executed_stage_names = [r["stage_name"] for r in execution.results]
        self.assertEqual(executed_stage_names, STAGES_LIST)

    def test_all_9_stages_use_real_capability_bindings(self):
        execution = self.wf_engine.execute_workflow("memory_optimization")

        expected_managers = {
            "memory_analysis": "MemoryAnalysisManager",
            "priority_evaluation": "MemoryPriorityManager",
            "simulation": "SimulationManager",
            "governance_check": "GovernanceManager",
            "decision_generation": "MaintenanceDecisionManager",
            "execution_planning": "MaintenanceExecutionManager",
            "validation": "ExecutionValidationManager",
            "feedback_generation": "ExecutionFeedbackManager",
            "learning_update": "StrategyLearningManager",
        }

        for res in execution.results:
            stage_name = res["stage_name"]
            expected_mgr = expected_managers[stage_name]
            self.assertEqual(res["manager_name"], expected_mgr, f"Stage {stage_name} expected {expected_mgr}")
            self.assertEqual(res["status"], "completed")
            self.assertIsNotNone(res.get("data"))

    def test_persisted_results_and_read_only_guarantee(self):
        initial_memories = self.db_manager.get_all_memories_for_audit()
        self.wf_engine.execute_workflow("memory_optimization")
        post_memories = self.db_manager.get_all_memories_for_audit()

        self.assertEqual(len(initial_memories), len(post_memories))

        capability_results = self.db_manager.get_capability_results()
        self.assertEqual(len(capability_results), 9)


if __name__ == "__main__":
    unittest.main()
