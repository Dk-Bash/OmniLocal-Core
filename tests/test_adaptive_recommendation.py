import unittest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_strategy_evaluation.models import StrategyEvaluation
from maintenance_strategy_evaluation.manager import StrategyEvaluationManager
from maintenance_strategy_learning.manager import StrategyLearningManager
from maintenance_strategy.manager import MaintenanceStrategyManager
from maintenance_adaptive.models import AdaptiveRecommendation
from maintenance_adaptive.manager import AdaptiveRecommendationManager


class TestAdaptiveRecommendation(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db = SQLiteManager(db_path=self.db_path)
        self.db.create_tables()

        self.eval_manager = StrategyEvaluationManager(db_manager=self.db)
        self.learning_manager = StrategyLearningManager(evaluation_manager=self.eval_manager)
        self.strategy_manager = MaintenanceStrategyManager()
        self.adaptive_manager = AdaptiveRecommendationManager(
            learning_manager=self.learning_manager,
            strategy_manager=self.strategy_manager,
            db_manager=self.db,
        )

    def tearDown(self):
        self.db.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_recommendation_without_history(self):
        """Prueba que sin historial la recomendación asigna confidence=0.0 y based_on_history=False."""
        rec = self.adaptive_manager.generate_recommendation()

        self.assertIsInstance(rec, AdaptiveRecommendation)
        self.assertEqual(rec.confidence, 0.0)
        self.assertFalse(rec.based_on_history)
        self.assertEqual(rec.strategy_type, "unknown")
        self.assertIn("No hay suficiente aprendizaje", rec.recommended_action)

    def test_recommendation_with_historical_learning(self):
        """Prueba que con evaluaciones históricas se selecciona la mejor estrategia con confidence > 0.0 y based_on_history=True."""
        # Crear evaluaciones históricas
        eval_planned = StrategyEvaluation(
            strategy_id="planned_001",
            quality_score=0.6,
            impact_score=0.6,
            confidence_score=0.7,
            summary="Estrategia planificada razonable"
        )
        eval_soon = StrategyEvaluation(
            strategy_id="soon_001",
            quality_score=0.8,
            impact_score=0.8,
            confidence_score=0.8,
            summary="Estrategia próxima de alto impacto"
        )
        eval_immediate = StrategyEvaluation(
            strategy_id="immediate_001",
            quality_score=1.0,
            impact_score=1.0,
            confidence_score=0.9,
            summary="Estrategia inmediata de máxima efectividad"
        )

        self.eval_manager.evaluate_strategy(eval_planned)
        self.eval_manager.evaluate_strategy(eval_soon)
        self.eval_manager.evaluate_strategy(eval_immediate)

        rec = self.adaptive_manager.generate_recommendation()

        self.assertIsInstance(rec, AdaptiveRecommendation)
        self.assertEqual(rec.strategy_type, "immediate")
        self.assertGreater(rec.confidence, 0.0)
        self.assertEqual(rec.confidence, 0.95)
        self.assertTrue(rec.based_on_history)
        self.assertIn("immediate", rec.recommended_action)

    def test_sqlite_persistence(self):
        """Prueba las funciones CRUD de sqlite_manager para recomendaciones adaptativas."""
        rec = AdaptiveRecommendation(
            strategy_type="immediate",
            recommended_action="Ejecutar estrategia adaptativa inmediata",
            confidence=0.95,
            reason="Prueba de persistencia",
            based_on_history=True
        )

        rec_id = self.db.insert_adaptive_recommendation(rec)
        self.assertIsInstance(rec_id, int)
        self.assertGreater(rec_id, 0)

        saved_rec = self.db.get_adaptive_recommendation(rec_id)
        self.assertIsNotNone(saved_rec)
        self.assertEqual(saved_rec["strategy_type"], "immediate")
        self.assertEqual(saved_rec["confidence"], 0.95)
        self.assertTrue(saved_rec["based_on_history"])

        all_recs = self.db.get_adaptive_recommendations()
        self.assertEqual(len(all_recs), 1)

    def test_integrity_no_modifications(self):
        """Garantía de integridad: no modifica memorias, ni evaluaciones, ni eventos de auditoría."""
        initial_eval_count = self.db.count_strategy_evaluations()
        initial_memory_count = self.db.count_memories()
        initial_audit_count = len(self.db.get_all_audit_events())

        # Generar recomendación
        _ = self.adaptive_manager.generate_recommendation()

        self.assertEqual(self.db.count_strategy_evaluations(), initial_eval_count)
        self.assertEqual(self.db.count_memories(), initial_memory_count)
        self.assertEqual(len(self.db.get_all_audit_events()), initial_audit_count)


if __name__ == "__main__":
    unittest.main()
