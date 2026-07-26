import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.manager import MaintenanceManager
from memory_planning.models import MaintenanceTask, MaintenancePlan
from memory_planning.manager import MaintenancePlanningManager


class TestMemoryPlanning(unittest.TestCase):
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

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_empty_plan_without_issues(self):
        """Probar que un sistema sin problemas genera un plan con total_tasks = 0."""
        plan = self.planning_manager.create_plan()
        self.assertIsInstance(plan, MaintenancePlan)
        self.assertEqual(plan.total_tasks, 0)
        self.assertEqual(plan.high_priority_tasks, 0)
        self.assertEqual(plan.medium_priority_tasks, 0)
        self.assertEqual(len(plan.tasks), 0)

    def test_plan_with_empty_memory_and_duplicate(self):
        """Probar plan con memoria vacía y duplicado -> total_tasks = 2."""
        # 1. Duplicado
        self.memory_manager.save_memory("Nota idéntica", "semantic", 0.6)
        self.memory_manager.save_memory("Nota idéntica", "semantic", 0.6)

        # 2. Memoria vacía
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("", "episodic", 0.5)
        )
        conn.commit()

        plan = self.planning_manager.create_plan()
        self.assertEqual(plan.total_tasks, 2)
        self.assertEqual(len(plan.tasks), 2)

        task_types = [t.task_type for t in plan.tasks]
        self.assertIn("empty_memory_review", task_types)
        self.assertIn("duplicate_review", task_types)

        # Verificar estados por defecto
        for t in plan.tasks:
            self.assertEqual(t.status, "pending")

    def test_priority_counts_and_task_conversion(self):
        """Validar conteo exacto de high_priority_tasks y medium_priority_tasks."""
        # 1. Duplicado (medium priority)
        self.memory_manager.save_memory("Dato duplicado", "semantic", 0.7)
        self.memory_manager.save_memory("Dato duplicado", "semantic", 0.7)

        # 2. Memoria vacía (high priority)
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("   ", "episodic", 0.4)
        )

        # 3. Importancia inválida (high priority)
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("Importancia mala", "semantic", 3.0)
        )
        conn.commit()

        plan = self.planning_manager.create_plan()
        self.assertEqual(plan.total_tasks, 3)
        self.assertEqual(plan.high_priority_tasks, 2)
        self.assertEqual(plan.medium_priority_tasks, 1)

        task_map = {t.task_type: t for t in plan.tasks}
        self.assertIn("empty_memory_review", task_map)
        self.assertEqual(task_map["empty_memory_review"].priority, "high")

        self.assertIn("importance_fix", task_map)
        self.assertEqual(task_map["importance_fix"].priority, "high")

        self.assertIn("duplicate_review", task_map)
        self.assertEqual(task_map["duplicate_review"].priority, "medium")


if __name__ == "__main__":
    unittest.main()
