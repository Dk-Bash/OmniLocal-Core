import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.manager import MaintenanceManager
from memory_planning.manager import MaintenancePlanningManager
from memory_priority.manager import MemoryPriorityManager
from memory_governance.models import MaintenanceApproval
from memory_governance.manager import GovernanceManager


class TestMemoryGovernance(unittest.TestCase):
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

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_no_tasks_empty_evaluations(self):
        """Probar que sin tareas el resultado es una lista vacía."""
        approvals = self.governance_manager.evaluate_tasks()
        self.assertIsInstance(approvals, list)
        self.assertEqual(len(approvals), 0)

    def test_critical_and_medium_and_high_tasks(self):
        """Probar evaluaciones para tareas critical (empty memory), high (importance fix) y medium (duplicate)."""
        # 1. Duplicado (medium priority -> risk: low, approval: approved)
        self.memory_manager.save_memory("Texto duplicado", "semantic", 0.5)
        self.memory_manager.save_memory("Texto duplicado", "semantic", 0.5)

        # 2. Memoria vacía (critical priority -> risk: high, approval: requires_review)
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("", "episodic", 0.5)
        )

        # 3. Importancia inválida (high priority -> risk: medium, approval: requires_review)
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("Mala importancia", "semantic", 2.5)
        )
        conn.commit()

        approvals = self.governance_manager.evaluate_tasks()
        self.assertEqual(len(approvals), 3)

        app_map = {a.task_type: a for a in approvals}

        # empty_memory_review (critical priority)
        self.assertIn("empty_memory_review", app_map)
        self.assertEqual(app_map["empty_memory_review"].risk_level, "high")
        self.assertEqual(app_map["empty_memory_review"].approval_status, "requires_review")

        # importance_fix (high priority)
        self.assertIn("importance_fix", app_map)
        self.assertEqual(app_map["importance_fix"].risk_level, "medium")
        self.assertEqual(app_map["importance_fix"].approval_status, "requires_review")

        # duplicate_review (medium priority)
        self.assertIn("duplicate_review", app_map)
        self.assertEqual(app_map["duplicate_review"].risk_level, "low")
        self.assertEqual(app_map["duplicate_review"].approval_status, "approved")

    def test_risk_level_mapping_rules(self):
        """Validar directamente la transformación de riesgo: critical -> high, high -> medium, medium -> low."""
        # Se verifica nuevamente que la asignación corresponda exactamente a las especificaciones.
        self.memory_manager.save_memory("Item A", "semantic", 0.5)
        self.memory_manager.save_memory("Item A", "semantic", 0.5)

        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("   ", "episodic", 0.5)
        )
        conn.commit()

        approvals = self.governance_manager.evaluate_tasks()
        for app in approvals:
            if app.task_type == "empty_memory_review":
                self.assertEqual(app.risk_level, "high")
                self.assertEqual(app.approval_status, "requires_review")
            elif app.task_type == "duplicate_review":
                self.assertEqual(app.risk_level, "low")
                self.assertEqual(app.approval_status, "approved")


if __name__ == "__main__":
    unittest.main()
