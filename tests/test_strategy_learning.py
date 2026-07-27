import os
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_strategy_evaluation.manager import StrategyEvaluationManager
from maintenance_strategy_learning.manager import StrategyLearningManager
from maintenance_strategy_learning.models import StrategyLearningReport


class TestStrategyLearning:
    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        db_file = tmp_path / "test_omnilocal.db"
        self.db = SQLiteManager(db_path=str(db_file))
        self.db.create_tables()
        self.eval_manager = StrategyEvaluationManager(db_manager=self.db)
        self.manager = StrategyLearningManager(evaluation_manager=self.eval_manager)
        yield
        self.db.close()

    def test_empty_database_report(self):
        report = self.manager.generate_learning_report()
        assert isinstance(report, StrategyLearningReport)
        assert report.total_evaluations == 0
        assert report.average_quality_score == 0.0
        assert report.average_impact_score == 0.0
        assert report.average_confidence_score == 0.0
        assert report.best_strategy_type is None

    def test_multiple_evaluations_report(self):
        # Crear evaluaciones para immediate (1.0, 1.0, 0.9), soon (0.8, 0.8, 0.8), planned (0.6, 0.6, 0.7)
        self.eval_manager.evaluate_strategy("strategy_immediate")
        self.eval_manager.evaluate_strategy("strategy_soon")
        self.eval_manager.evaluate_strategy("strategy_planned")

        report = self.manager.generate_learning_report()
        assert report.total_evaluations == 3
        # Promedio calidad = (1.0 + 0.8 + 0.6) / 3 = 0.8
        assert pytest.approx(report.average_quality_score, 0.01) == 0.8
        # Promedio impacto = (1.0 + 0.8 + 0.6) / 3 = 0.8
        assert pytest.approx(report.average_impact_score, 0.01) == 0.8
        # Promedio confianza = (0.9 + 0.8 + 0.7) / 3 = 0.8
        assert pytest.approx(report.average_confidence_score, 0.01) == 0.8
        # Mejor estrategia esperada: immediate
        assert report.best_strategy_type == "immediate"

    def test_sqlite_analytical_methods(self):
        self.eval_manager.evaluate_strategy("strategy_immediate")
        self.eval_manager.evaluate_strategy("strategy_soon")

        assert self.db.count_strategy_evaluations() == 2
        assert pytest.approx(self.db.average_strategy_quality(), 0.01) == 0.9
        assert pytest.approx(self.db.average_strategy_impact(), 0.01) == 0.9
        assert pytest.approx(self.db.average_strategy_confidence(), 0.01) == 0.85
        assert self.db.get_best_strategy_type() == "immediate"

    def test_integrity_no_side_effects(self):
        initial_memories = self.db.count_memories()
        initial_audits = len(self.db.get_all_audit_events())

        self.eval_manager.evaluate_strategy("strategy_immediate")
        self.eval_manager.evaluate_strategy("strategy_soon")

        eval_count_before = self.db.count_strategy_evaluations()

        report = self.manager.generate_learning_report()
        assert isinstance(report, StrategyLearningReport)

        # Confirmar que generar reporte de aprendizaje no altera evaluaciones, ni auditorías, ni memorias
        assert self.db.count_strategy_evaluations() == eval_count_before
        assert self.db.count_memories() == initial_memories
        assert len(self.db.get_all_audit_events()) == initial_audits
