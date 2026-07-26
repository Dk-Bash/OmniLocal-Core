import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_integrity.models import IntegrityReport, MemoryIssue
from memory_integrity.manager import MemoryIntegrityManager


class TestMemoryIntegrity(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.memory_manager = MemoryManager(db_manager=self.db_manager)
        self.integrity_manager = MemoryIntegrityManager(
            memory_manager=self.memory_manager,
            db_manager=self.db_manager
        )

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_clean_database_audit(self):
        """Probar que en una base de datos limpia issues_found sea 0."""
        report = self.integrity_manager.audit_memory()
        self.assertIsInstance(report, IntegrityReport)
        self.assertEqual(report.total_checked, 0)
        self.assertEqual(report.issues_found, 0)
        self.assertEqual(len(report.issues), 0)

    def test_empty_content_detection(self):
        """Probar la detección de memorias con contenido vacío (empty_content)."""
        # Insertar directamente una memoria con contenido vacío
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("", "episodic", 0.5)
        )
        conn.commit()

        report = self.integrity_manager.audit_memory()
        self.assertEqual(report.total_checked, 1)
        self.assertEqual(report.issues_found, 1)
        self.assertEqual(report.issues[0].issue_type, "empty_content")
        self.assertEqual(report.issues[0].severity, "medium")

    def test_duplicate_content_detection(self):
        """Probar la detección de memorias con contenido duplicado exacto (duplicate_content)."""
        self.memory_manager.save_memory("Python es un lenguaje", "semantic", 0.8)
        self.memory_manager.save_memory("Python es un lenguaje", "semantic", 0.8)

        report = self.integrity_manager.audit_memory()
        self.assertEqual(report.total_checked, 2)
        self.assertEqual(report.issues_found, 1)
        self.assertEqual(report.issues[0].issue_type, "duplicate_content")

    def test_full_report_validation(self):
        """Probar un reporte completo con múltiples problemas detectados."""
        # 1. Memoria válida
        self.memory_manager.save_memory("Aprender TypeScript", "semantic", 0.9)

        # 2. Memoria duplicada
        self.memory_manager.save_memory("Aprender TypeScript", "semantic", 0.9)

        # 3. Memoria vacía
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("   ", "episodic", 0.5)
        )
        # 4. Importancia inválida
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("Memoria con importancia inválida", "semantic", 1.5)
        )
        conn.commit()

        report = self.integrity_manager.audit_memory()
        self.assertEqual(report.total_checked, 4)
        self.assertEqual(report.issues_found, 3)

        issue_types = [issue.issue_type for issue in report.issues]
        self.assertIn("duplicate_content", issue_types)
        self.assertIn("empty_content", issue_types)
        self.assertIn("invalid_importance", issue_types)


if __name__ == "__main__":
    unittest.main()
