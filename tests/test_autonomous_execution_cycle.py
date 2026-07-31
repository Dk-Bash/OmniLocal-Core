import unittest
import tempfile
import os
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.autonomous.manager import AutonomousWorkflowManager
from omnilocal_runtime.autonomous.models import AutonomousExecutionCycle


class TestAutonomousExecutionCycle(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_autonomous_cycle.db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

        self.auto_manager = AutonomousWorkflowManager(db_manager=self.db_manager)

    def tearDown(self):
        self.db_manager.close()
        self.temp_dir.cleanup()

    def test_start_cycle_initialization(self):
        cycle = self.auto_manager.start_cycle("memory_optimization")

        self.assertIsNotNone(cycle.id)
        self.assertEqual(cycle.workflow_id, "memory_optimization")
        self.assertEqual(cycle.status, "running")
        self.assertEqual(cycle.completed_stages, 0)
        self.assertEqual(cycle.failed_stages, 0)
        self.assertEqual(cycle.total_stages, 9)
        self.assertEqual(cycle.success_rate, 0.0)

    def test_execute_full_autonomous_cycle(self):
        cycle = self.auto_manager.execute_cycle("memory_optimization")

        self.assertIsNotNone(cycle.id)
        self.assertEqual(cycle.status, "completed")
        self.assertEqual(cycle.completed_stages, 9)
        self.assertEqual(cycle.failed_stages, 0)
        self.assertEqual(cycle.total_stages, 9)
        self.assertEqual(cycle.success_rate, 100.0)
        self.assertEqual(len(cycle.details), 9)

    def test_cycle_persistence_and_retrieval(self):
        executed_cycle = self.auto_manager.execute_cycle("memory_optimization")

        retrieved = self.auto_manager.get_cycle(executed_cycle.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, executed_cycle.id)
        self.assertEqual(retrieved.status, "completed")
        self.assertEqual(retrieved.completed_stages, 9)
        self.assertEqual(retrieved.success_rate, 100.0)

        all_cycles = self.auto_manager.get_cycles()
        self.assertTrue(len(all_cycles) >= 1)
        self.assertEqual(all_cycles[0]["id"], executed_cycle.id)


if __name__ == "__main__":
    unittest.main()
