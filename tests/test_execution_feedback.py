import os
import tempfile
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_tracking.manager import ExecutionTrackingManager
from maintenance_result.manager import ExecutionResultManager
from maintenance_feedback.models import ExecutionFeedback
from maintenance_feedback.manager import ExecutionFeedbackManager


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = SQLiteManager(db_path=path)
    db.create_tables()
    yield db
    db.close()
    if os.path.exists(path):
        os.remove(path)


def test_feedback_for_success_result(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    res_mgr = ExecutionResultManager(db_manager=temp_db, tracking_manager=track_mgr)
    fb_mgr = ExecutionFeedbackManager(db_manager=temp_db, result_manager=res_mgr)

    tracking = track_mgr.create_tracking()
    track_mgr.update_status(tracking.id, status="completed", progress=1.0)
    result = res_mgr.evaluate_result(tracking_id=tracking.id)

    feedback = fb_mgr.generate_feedback(result_id=result.id)

    assert feedback.id is not None
    assert feedback.result_id == result.id
    assert feedback.feedback_type == "positive"
    assert feedback.quality_score == 0.9
    assert "positiva" in feedback.learning_notes.lower()


def test_feedback_for_partial_result(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    res_mgr = ExecutionResultManager(db_manager=temp_db, tracking_manager=track_mgr)
    fb_mgr = ExecutionFeedbackManager(db_manager=temp_db, result_manager=res_mgr)

    tracking = track_mgr.create_tracking()
    track_mgr.update_status(tracking.id, status="running", progress=0.5)
    result = res_mgr.evaluate_result(tracking_id=tracking.id)

    feedback = fb_mgr.generate_feedback(result_id=result.id)

    assert feedback.feedback_type == "neutral"
    assert feedback.quality_score == 0.5


def test_feedback_for_failed_result(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    res_mgr = ExecutionResultManager(db_manager=temp_db, tracking_manager=track_mgr)
    fb_mgr = ExecutionFeedbackManager(db_manager=temp_db, result_manager=res_mgr)

    tracking = track_mgr.create_tracking()
    track_mgr.update_status(tracking.id, status="failed", progress=0.2)
    result = res_mgr.evaluate_result(tracking_id=tracking.id)

    feedback = fb_mgr.generate_feedback(result_id=result.id)

    assert feedback.feedback_type == "negative"
    assert feedback.quality_score == 0.1


def test_complete_lifecycle_flow(temp_db):
    # Probar flujo completo Bloque 8: Tracking -> Result -> Feedback
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    res_mgr = ExecutionResultManager(db_manager=temp_db, tracking_manager=track_mgr)
    fb_mgr = ExecutionFeedbackManager(db_manager=temp_db, result_manager=res_mgr)

    # 1. Tracking
    tracking = track_mgr.create_tracking()
    track_mgr.update_status(tracking.id, status="running", progress=0.8)
    track_mgr.update_status(tracking.id, status="completed", progress=1.0)

    # 2. Result
    result = res_mgr.evaluate_result(tracking_id=tracking.id)

    # 3. Feedback
    feedback = fb_mgr.generate_feedback(result_id=result.id)

    assert tracking.id is not None
    assert result.result_status == "success"
    assert feedback.quality_score == 0.9

    # Verificar todo en base de datos
    trackings = temp_db.get_execution_trackings()
    results = temp_db.get_execution_results()
    feedbacks = temp_db.get_execution_feedbacks()

    assert len(trackings) >= 1
    assert len(results) >= 1
    assert len(feedbacks) >= 1
