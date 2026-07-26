import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.models import MaintenanceRecommendation
from memory_maintenance.manager import MaintenanceManager


class TestMemoryMaintenance(unittest.TestCase):
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

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_no_issues_empty_recommendations(self):
        """Probar que cuando no hay problemas en memoria se retorna una lista vacía."""
        recs = self.maintenance_manager.generate_recommendations()
        self.assertEqual(recs, [])

    def test_duplicate_recommendation(self):
        """Probar recomendación para contenido duplicado (duplicate_content -> medium priority)."""
        self.memory_manager.save_memory("Nota duplicada de prueba", "semantic", 0.7)
        self.memory_manager.save_memory("Nota duplicada de prueba", "semantic", 0.7)

        recs = self.maintenance_manager.generate_recommendations()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].issue_type, "duplicate_content")
        self.assertEqual(recs[0].recommendation, "Considerar fusionar memorias duplicadas")
        self.assertEqual(recs[0].priority, "medium")

    def test_empty_content_recommendation(self):
        """Probar recomendación para contenido vacío (empty_content -> high priority)."""
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("", "episodic", 0.5)
        )
        conn.commit()

        recs = self.maintenance_manager.generate_recommendations()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].issue_type, "empty_content")
        self.assertEqual(recs[0].recommendation, "Revisar memoria sin contenido")
        self.assertEqual(recs[0].priority, "high")

    def test_priorities_and_mixed_issues(self):
        """Probar la generación de recomendaciones y validación de prioridades para múltiples problemas."""
        # 1. Duplicados
        self.memory_manager.save_memory("Regla de negocio", "semantic", 0.8)
        self.memory_manager.save_memory("Regla de negocio", "semantic", 0.8)

        # 2. Memoria vacía
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("   ", "episodic", 0.5)
        )

        # 3. Importancia inválida
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("Importancia fuera de rango", "semantic", 2.5)
        )
        conn.commit()

        recs = self.maintenance_manager.generate_recommendations()
        self.assertEqual(len(recs), 3)

        rec_map = {r.issue_type: r for r in recs}
        self.assertIn("duplicate_content", rec_map)
        self.assertEqual(rec_map["duplicate_content"].priority, "medium")

        self.assertIn("empty_content", rec_map)
        self.assertEqual(rec_map["empty_content"].priority, "high")

        self.assertIn("invalid_importance", rec_map)
        self.assertEqual(rec_map["invalid_importance"].priority, "high")
        self.assertEqual(rec_map["invalid_importance"].recommendation, "Corregir nivel de importancia")


if __name__ == "__main__":
    unittest.main()
