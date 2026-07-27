import os
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_strategy_evaluation.manager import StrategyEvaluationManager
from maintenance_strategy_evaluation.models import StrategyEvaluation


class TestStrategyEvaluation:
    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        db_file = tmp_path / "test_omnilocal.db"
        self.db = SQLiteManager(db_path=str(db_file))
        self.db.create_tables()
        self.manager = StrategyEvaluationManager(db_manager=self.db)
        yield
        self.db.close()

    def test_immediate_strategy_evaluation(self):
        eval_res = self.manager.evaluate_strategy("strategy_immediate")
        assert isinstance(eval_res, StrategyEvaluation)
        assert eval_res.quality_score == 1.0
        assert eval_res.impact_score == 1.0
        assert eval_res.confidence_score == 0.9
        assert eval_res.id is not None

    def test_soon_strategy_evaluation(self):
        eval_res = self.manager.evaluate_strategy("strategy_soon")
        assert eval_res.quality_score == 0.8
        assert eval_res.impact_score == 0.8
        assert eval_res.confidence_score == 0.8

    def test_planned_strategy_evaluation(self):
        eval_res = self.manager.evaluate_strategy("strategy_planned")
        assert eval_res.quality_score == 0.6
        assert eval_res.impact_score == 0.6
        assert eval_res.confidence_score == 0.7

    def test_deferred_strategy_evaluation(self):
        eval_res = self.manager.evaluate_strategy("strategy_deferred")
        assert eval_res.quality_score == 0.3
        assert eval_res.impact_score == 0.3
        assert eval_res.confidence_score == 0.5

    def test_integrity_no_side_effects(self):
        initial_memories = self.db.count_memories()
        initial_audits = len(self.db.get_all_audit_events())

        self.manager.evaluate_strategy("strategy_immediate")
        self.manager.evaluate_strategy("strategy_soon")

        assert self.db.count_memories() == initial_memories
        assert len(self.db.get_all_audit_events()) == initial_audits
