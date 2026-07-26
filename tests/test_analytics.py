import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from analytics.models import SystemMetrics
from analytics.manager import AnalyticsManager
from evaluation.manager import EvaluationManager
from memory.manager import MemoryManager
from context.manager import ContextManager


class TestAnalytics(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.analytics_manager = AnalyticsManager(db_manager=self.db_manager)
        self.eval_manager = EvaluationManager(db_manager=self.db_manager)
        self.memory_manager = MemoryManager(db_manager=self.db_manager)
        self.context_manager = ContextManager(db_manager=self.db_manager)

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_empty_metrics(self):
        """Prueba que con una base de datos limpia devuelva métricas en 0 y 0.0."""
        metrics = self.analytics_manager.get_system_metrics()
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertEqual(metrics.total_memories, 0)
        self.assertEqual(metrics.total_sessions, 0)
        self.assertEqual(metrics.total_interactions, 0)
        self.assertEqual(metrics.average_feedback_score, 0.0)

    def test_metrics_with_data(self):
        """Prueba la contabilización correcta de memorias, sesiones e interacciones."""
        # Insertar memorias (una episodic, una semantic)
        self.memory_manager.save_memory(
            content="Prueba de interacción episódica",
            memory_type="episodic",
            importance=0.8
        )
        self.memory_manager.save_memory(
            content="Conocimiento conceptual de Python",
            memory_type="semantic",
            importance=0.9
        )

        # Crear una sesión de contexto
        self.context_manager.create_session("Sesión de Pruebas")

        metrics = self.analytics_manager.get_system_metrics()
        self.assertEqual(metrics.total_memories, 2)
        self.assertEqual(metrics.total_sessions, 1)
        self.assertEqual(metrics.total_interactions, 1)  # Solo la de tipo episodic

    def test_average_feedback_score(self):
        """Prueba el cálculo del promedio de rating (e.g. 5 + 3 -> 4.0)."""
        self.eval_manager.add_feedback(
            interaction_id=1,
            rating=5,
            confidence=0.9,
            comment="Excelente"
        )
        self.eval_manager.add_feedback(
            interaction_id=2,
            rating=3,
            confidence=0.7,
            comment="Regular"
        )

        metrics = self.analytics_manager.get_system_metrics()
        self.assertEqual(metrics.average_feedback_score, 4.0)


if __name__ == "__main__":
    unittest.main()
