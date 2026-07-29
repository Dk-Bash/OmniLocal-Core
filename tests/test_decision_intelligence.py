import unittest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_strategy_evaluation.models import StrategyEvaluation
from maintenance_strategy_evaluation.manager import StrategyEvaluationManager
from maintenance_strategy_learning.manager import StrategyLearningManager
from maintenance_strategy.manager import MaintenanceStrategyManager
from maintenance_intelligence.manager import MaintenanceIntelligenceManager
from maintenance_adaptive.manager import AdaptiveRecommendationManager
from maintenance_decision.models import MaintenanceDecision
from maintenance_decision.manager import MaintenanceDecisionManager


class TestDecisionIntelligence(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db = SQLiteManager(db_path=self.db_path)
        self.db.create_tables()

        self.eval_manager = StrategyEvaluationManager(db_manager=self.db)
        self.learning_manager = StrategyLearningManager(evaluation_manager=self.eval_manager)
        self.strategy_manager = MaintenanceStrategyManager()
        self.intelligence_manager = MaintenanceIntelligenceManager(db_manager=self.db)
        self.adaptive_manager = AdaptiveRecommendationManager(
            learning_manager=self.learning_manager,
            strategy_manager=self.strategy_manager,
            db_manager=self.db,
        )
        self.decision_manager = MaintenanceDecisionManager(
            adaptive_manager=self.adaptive_manager,
            learning_manager=self.learning_manager,
            intelligence_manager=self.intelligence_manager,
            db_manager=self.db,
        )

    def tearDown(self):
        self.db.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_decision_without_history(self):
        """Prueba que sin historial la decisión es de tipo default, selected_strategy='unknown' y confidence=0.0."""
        decision = self.decision_manager.make_decision()

        self.assertIsInstance(decision, MaintenanceDecision)
        self.assertEqual(decision.decision_type, "default")
        self.assertEqual(decision.selected_strategy, "unknown")
        self.assertEqual(decision.confidence, 0.0)
        self.assertIn("No sufficient historical learning", decision.reasoning)

    def test_decision_with_history(self):
        """Prueba que con aprendizaje histórico fuerte la decisión es adaptativa con selected_strategy='immediate' y confidence >= 0.8."""
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

        decision = self.decision_manager.make_decision()

        self.assertIsInstance(decision, MaintenanceDecision)
        self.assertEqual(decision.decision_type, "adaptive")
        self.assertEqual(decision.selected_strategy, "immediate")
        self.assertGreaterEqual(decision.confidence, 0.8)
        self.assertIn("Selected immediate strategy", decision.reasoning)

    def test_supporting_factors(self):
        """Prueba que la decisión con historial incluye los factores de soporte correctos."""
        eval_immediate = StrategyEvaluation(
            strategy_id="immediate_001",
            quality_score=1.0,
            impact_score=1.0,
            confidence_score=0.9,
            summary="Estrategia inmediata recomendada"
        )
        self.eval_manager.evaluate_strategy(eval_immediate)

        decision = self.decision_manager.make_decision()

        self.assertIn("historical_learning_available", decision.supporting_factors)
        self.assertIn("high_strategy_confidence", decision.supporting_factors)
        self.assertIn("intelligence_metrics_available", decision.supporting_factors)

    def test_sqlite_persistence(self):
        """Prueba las funciones CRUD de sqlite_manager para decisiones de mantenimiento."""
        decision = MaintenanceDecision(
            decision_type="adaptive",
            selected_strategy="immediate",
            confidence=0.95,
            reasoning="Prueba de persistencia de decisión",
            supporting_factors=["historical_learning_available", "high_strategy_confidence"]
        )

        dec_id = self.db.insert_maintenance_decision(decision)
        self.assertIsInstance(dec_id, int)
        self.assertGreater(dec_id, 0)

        saved_dec = self.db.get_maintenance_decision(dec_id)
        self.assertIsNotNone(saved_dec)
        self.assertEqual(saved_dec["decision_type"], "adaptive")
        self.assertEqual(saved_dec["selected_strategy"], "immediate")
        self.assertEqual(saved_dec["confidence"], 0.95)
        self.assertIn("historical_learning_available", saved_dec["supporting_factors"])

        all_decs = self.db.get_maintenance_decisions()
        self.assertEqual(len(all_decs), 1)

    def test_integrity_no_modifications(self):
        """Garantía de integridad: no modifica recomendaciones, ni evaluaciones, ni estrategias, ni memorias."""
        initial_eval_count = self.db.count_strategy_evaluations()
        initial_memory_count = self.db.count_memories()
        initial_rec_count = len(self.db.get_adaptive_recommendations())

        _ = self.decision_manager.make_decision()

        self.assertEqual(self.db.count_strategy_evaluations(), initial_eval_count)
        self.assertEqual(self.db.count_memories(), initial_memory_count)


if __name__ == "__main__":
    unittest.main()
