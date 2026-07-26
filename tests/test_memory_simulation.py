import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.manager import MaintenanceManager
from memory_planning.manager import MaintenancePlanningManager
from memory_priority.manager import MemoryPriorityManager
from memory_governance.manager import GovernanceManager
from memory_simulation.models import SimulationResult
from memory_simulation.manager import SimulationManager


class TestMemorySimulation(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.memory_manager = MemoryManager(db_manager=self.db_manager)
        self.integrity_manager = MemoryIntegrityManager(
            memory_manager=self.memory_manager,
            db_manager=self.db_manager
        )
        self.maintenance_manager = MaintenanceManager(
            integrity_manager=self.integrity_manager
        )
        self.planning_manager = MaintenancePlanningManager(
            maintenance_manager=self.maintenance_manager
        )
        self.priority_manager = MemoryPriorityManager(
            planning_manager=self.planning_manager
        )
        self.governance_manager = GovernanceManager(
            priority_manager=self.priority_manager
        )
        self.simulation_manager = SimulationManager(
            governance_manager=self.governance_manager
        )

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_no_tasks_empty_simulation(self):
        """Probar que sin tareas la simulación retorna una lista vacía."""
        results = self.simulation_manager.simulate()
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_approved_and_blocked_simulation_statuses(self):
        """Probar que las tareas duplicadas obtienen status 'simulated' y las críticas 'blocked'."""
        # Tarea duplicada (approved -> simulated)
        self.memory_manager.save_memory("Memoria repetida", "semantic", 0.5)
        self.memory_manager.save_memory("Memoria repetida", "semantic", 0.5)

        # Tarea vacía (requires_review -> blocked)
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("", "episodic", 0.5)
        )
        conn.commit()

        results = self.simulation_manager.simulate()
        self.assertEqual(len(results), 2)

        res_map = {r.task_type: r for r in results}

        # duplicate_review -> simulated
        self.assertIn("duplicate_review", res_map)
        self.assertEqual(res_map["duplicate_review"].simulation_status, "simulated")
        self.assertIn("Reducir", res_map["duplicate_review"].expected_impact)

        # empty_memory_review -> blocked
        self.assertIn("empty_memory_review", res_map)
        self.assertEqual(res_map["empty_memory_review"].simulation_status, "blocked")
        self.assertEqual(res_map["empty_memory_review"].expected_impact, "Revisión requerida antes de modificar")

    def test_simulation_does_not_modify_data(self):
        """Validar strictly que la ejecución de la simulación no modifica ninguna memoria de la base de datos."""
        # Crear memoria inicial
        m1 = self.memory_manager.save_memory("Texto inicial intacto", "semantic", 0.7)
        m2 = self.memory_manager.save_memory("Texto inicial intacto", "semantic", 0.7)

        # Contar total antes de simulación
        memories_before = self.memory_manager.get_all_memories()
        self.assertEqual(len(memories_before), 2)

        # Ejecutar simulación
        sim_results = self.simulation_manager.simulate()
        self.assertTrue(len(sim_results) > 0)

        # Comprobar estado después de simulación
        memories_after = self.memory_manager.get_all_memories()
        self.assertEqual(len(memories_after), 2)
        self.assertEqual(memories_before[0].content, memories_after[0].content)
        self.assertEqual(memories_before[1].content, memories_after[1].content)


if __name__ == "__main__":
    unittest.main()
