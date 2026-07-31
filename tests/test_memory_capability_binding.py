import unittest
import tempfile
import os
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.engine import OmniLocalEngine
from omnilocal_runtime.workflows.engine import WorkflowEngine
from omnilocal_runtime.bindings.manager import CapabilityBindingManager
from omnilocal_runtime.bindings.memory_binding import (
    MemoryCapabilityBinding,
    MemoryIntelligenceManager,
    MemoryPriorityManager,
    MemorySimulationManager,
)


class TestMemoryCapabilityBinding(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_mem_binding.db")
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

    def test_registered_bindings_mapping(self):
        analysis_b = self.binding_manager.get_binding("memory_analysis")
        self.assertIsNotNone(analysis_b)
        self.assertEqual(analysis_b["manager_name"], "MemoryAnalysisManager")

        priority_b = self.binding_manager.get_binding("priority_evaluation")
        self.assertIsNotNone(priority_b)
        self.assertEqual(priority_b["manager_name"], "MemoryPriorityManager")

        simulation_b = self.binding_manager.get_binding("simulation")
        self.assertIsNotNone(simulation_b)
        self.assertEqual(simulation_b["manager_name"], "SimulationManager")

    def test_direct_stage_execution(self):
        res_analysis = self.binding_manager.execute_binding("memory_analysis")
        self.assertTrue(res_analysis.success)
        self.assertEqual(res_analysis.manager_name, "MemoryAnalysisManager")
        self.assertIn("total_memories", str(res_analysis.data))

        res_priority = self.binding_manager.execute_binding("priority_evaluation")
        self.assertTrue(res_priority.success)
        self.assertEqual(res_priority.manager_name, "MemoryPriorityManager")

        res_sim = self.binding_manager.execute_binding("simulation")
        self.assertTrue(res_sim.success)
        self.assertEqual(res_sim.manager_name, "SimulationManager")

    def test_workflow_execution_with_real_capabilities(self):
        execution = self.wf_engine.execute_workflow("memory_optimization")

        self.assertEqual(execution.status, "completed")
        self.assertEqual(len(execution.results), 9)

        # Verificar que memory_analysis usó el manager real de análisis de memoria
        analysis_stage = next(r for r in execution.results if r["stage_name"] == "memory_analysis")
        self.assertEqual(analysis_stage["manager_name"], "MemoryAnalysisManager")
        self.assertIn("total_memories", str(analysis_stage["data"]))

        # Verificar que priority_evaluation usó el manager real de prioridades
        priority_stage = next(r for r in execution.results if r["stage_name"] == "priority_evaluation")
        self.assertEqual(priority_stage["manager_name"], "MemoryPriorityManager")

        # Verificar que simulation usó el manager real de simulación
        sim_stage = next(r for r in execution.results if r["stage_name"] == "simulation")
        self.assertEqual(sim_stage["manager_name"], "SimulationManager")

        # Verificar que se registraron resultados en la tabla runtime_capability_results
        saved_results = self.db_manager.get_capability_results()
        self.assertTrue(len(saved_results) >= 3)

    def test_read_only_integrity_guarantee(self):
        initial_memories = self.db_manager.get_all_memories_for_audit()
        self.wf_engine.execute_workflow("memory_optimization")
        post_memories = self.db_manager.get_all_memories_for_audit()

        self.assertEqual(len(initial_memories), len(post_memories))


if __name__ == "__main__":
    unittest.main()
