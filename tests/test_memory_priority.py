import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.manager import MaintenanceManager
from memory_planning.manager import MaintenancePlanningManager
from memory_priority.models import PrioritizedTask, PriorityReport
from memory_priority.manager import MemoryPriorityManager


class TestMemoryPriority(unittest.TestCase):
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

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_no_tasks_empty_report(self):
        """Probar que sin tareas el reporte retorna total_tasks = 0."""
        report = self.priority_manager.prioritize()
        self.assertIsInstance(report, PriorityReport)
        self.assertEqual(report.total_tasks, 0)
        self.assertEqual(report.critical_tasks, 0)
        self.assertEqual(report.high_tasks, 0)
        self.assertEqual(report.medium_tasks, 0)
        self.assertEqual(report.low_tasks, 0)
        self.assertEqual(len(report.tasks), 0)

    def test_full_prioritization_and_counts(self):
        """Probar priorización completa con memoria vacía, duplicado e importancia inválida."""
        # 1. Duplicado (medium)
        self.memory_manager.save_memory("Texto duplicado", "semantic", 0.5)
        self.memory_manager.save_memory("Texto duplicado", "semantic", 0.5)

        # 2. Memoria vacía (critical)
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("", "episodic", 0.5)
        )

        # 3. Importancia inválida (high)
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("Mala importancia", "semantic", 2.5)
        )
        conn.commit()

        report = self.priority_manager.prioritize()
        self.assertEqual(report.total_tasks, 3)
        self.assertEqual(report.critical_tasks, 1)
        self.assertEqual(report.high_tasks, 1)
        self.assertEqual(report.medium_tasks, 1)
        self.assertEqual(report.low_tasks, 0)

    def test_score_and_level_validation(self):
        """Comprobar scores numéricos y niveles exactos asignados por tipo de tarea."""
        # 1. Duplicado -> 0.6 (medium)
        self.memory_manager.save_memory("Texto A", "semantic", 0.5)
        self.memory_manager.save_memory("Texto A", "semantic", 0.5)

        # 2. Memoria vacía -> 0.9 (critical)
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("   ", "episodic", 0.5)
        )

        # 3. Importancia inválida -> 0.85 (high)
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("Contenido ok", "semantic", -0.5)
        )
        conn.commit()

        report = self.priority_manager.prioritize()
        task_map = {t.task_type: t for t in report.tasks}

        # empty_memory_review = 0.9, critical
        self.assertIn("empty_memory_review", task_map)
        self.assertAlmostEqual(task_map["empty_memory_review"].priority_score, 0.9)
        self.assertEqual(task_map["empty_memory_review"].priority_level, "critical")

        # importance_fix = 0.85, high
        self.assertIn("importance_fix", task_map)
        self.assertAlmostEqual(task_map["importance_fix"].priority_score, 0.85)
        self.assertEqual(task_map["importance_fix"].priority_level, "high")

        # duplicate_review = 0.6, medium
        self.assertIn("duplicate_review", task_map)
        self.assertAlmostEqual(task_map["duplicate_review"].priority_score, 0.6)
        self.assertEqual(task_map["duplicate_review"].priority_level, "medium")


if __name__ == "__main__":
    unittest.main()
