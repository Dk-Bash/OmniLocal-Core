import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_analysis.models import MemoryAnalysis
from memory_analysis.manager import MemoryAnalysisManager


class TestMemoryAnalysis(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.memory_manager = MemoryManager(db_manager=self.db_manager)
        self.analysis_manager = MemoryAnalysisManager(
            memory_manager=self.memory_manager,
            db_manager=self.db_manager
        )

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_empty_memory_analysis(self):
        """Prueba que en una base limpia devuelva total_memories = 0 y average_importance = 0.0."""
        analysis = self.analysis_manager.analyze_memory()
        self.assertIsInstance(analysis, MemoryAnalysis)
        self.assertEqual(analysis.total_memories, 0)
        self.assertEqual(analysis.average_importance, 0.0)
        self.assertEqual(analysis.most_common_type, "none")
        self.assertEqual(analysis.memory_types, {})

    def test_mixed_memory_analysis(self):
        """Prueba análisis con memorias mezcladas (episodic 0.8, episodic 0.6, semantic 0.4)."""
        # Guardar 2 memorias episódicas
        self.memory_manager.save_memory(
            content="Primera interacción de usuario",
            memory_type="episodic",
            importance=0.8
        )
        self.memory_manager.save_memory(
            content="Segunda interacción de usuario",
            memory_type="episodic",
            importance=0.6
        )

        # Guardar 1 memoria semántica
        self.memory_manager.save_memory(
            content="Definición de concepto Python",
            memory_type="semantic",
            importance=0.4
        )

        analysis = self.analysis_manager.analyze_memory()
        self.assertEqual(analysis.total_memories, 3)
        self.assertEqual(analysis.most_common_type, "episodic")
        self.assertAlmostEqual(analysis.average_importance, 0.6, places=4)
        self.assertEqual(analysis.memory_types, {"episodic": 2, "semantic": 1})


if __name__ == "__main__":
    unittest.main()
