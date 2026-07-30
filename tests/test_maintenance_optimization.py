import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_optimization.models import OptimizationFeedback
from maintenance_optimization.manager import MaintenanceOptimizationManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_optimization_feedback_model_validations():
    # Valid model
    fb = OptimizationFeedback(
        decision_id=1,
        previous_confidence=0.70,
        new_confidence=0.85,
        improvement_score=0.15,
        optimization_type="improved",
        summary="Mejora detectada.",
    )
    assert fb.optimization_type == "improved"

    # Invalid optimization_type
    with pytest.raises(ValueError):
        OptimizationFeedback(
            decision_id=1,
            previous_confidence=0.70,
            new_confidence=0.85,
            improvement_score=0.15,
            optimization_type="unknown",
            summary="Error",
        )

    # Invalid confidence
    with pytest.raises(ValueError):
        OptimizationFeedback(
            decision_id=1,
            previous_confidence=-0.1,
            new_confidence=0.85,
            improvement_score=0.15,
            optimization_type="improved",
            summary="Error",
        )


def test_maintenance_optimization_manager_evaluation(temp_db):
    manager = MaintenanceOptimizationManager(db_manager=temp_db)
    feedbacks = manager.evaluate_optimization()

    assert len(feedbacks) > 0
    first_fb = feedbacks[0]
    assert first_fb.id is not None
    assert first_fb.optimization_type in {"improved", "stable", "degraded"}

    stored = manager.get_optimization_feedback(first_fb.id)
    assert stored is not None
    assert stored["optimization_type"] == first_fb.optimization_type

    history = manager.get_optimization_history()
    assert len(history) >= len(feedbacks)
