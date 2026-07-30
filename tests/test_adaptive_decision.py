import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_adaptive_decision.models import AdaptiveDecision
from maintenance_adaptive_decision.manager import AdaptiveDecisionManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_adaptive_decision_model_validations():
    # Valid model
    dec = AdaptiveDecision(
        correlation_id=1,
        decision_type="adaptive",
        recommended_strategy="planned",
        confidence=0.85,
        reasoning="Decisión adaptativa.",
    )
    assert dec.decision_type == "adaptive"

    # Invalid decision_type
    with pytest.raises(ValueError):
        AdaptiveDecision(
            correlation_id=1,
            decision_type="invalid_type",
            recommended_strategy="planned",
            confidence=0.85,
            reasoning="Error",
        )

    # Invalid confidence
    with pytest.raises(ValueError):
        AdaptiveDecision(
            correlation_id=1,
            decision_type="adaptive",
            recommended_strategy="planned",
            confidence=1.2,
            reasoning="Error",
        )


def test_adaptive_decision_manager_generation(temp_db):
    manager = AdaptiveDecisionManager(db_manager=temp_db)
    decisions = manager.generate_decisions()

    assert len(decisions) > 0
    first_dec = decisions[0]
    assert first_dec.id is not None
    assert first_dec.decision_type in {"adaptive", "conservative", "fallback"}

    stored = manager.get_adaptive_decision(first_dec.id)
    assert stored is not None
    assert stored["decision_type"] == first_dec.decision_type

    all_decs = manager.get_adaptive_decisions()
    assert len(all_decs) >= len(decisions)
