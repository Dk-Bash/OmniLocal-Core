import os
import tempfile
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_tracking.manager import ExecutionTrackingManager
from maintenance_result.models import ExecutionResult
from maintenance_result.manager import ExecutionResultManager


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


def test_evaluate_result_completed_tracking(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    res_mgr = ExecutionResultManager(db_manager=temp_db, tracking_manager=track_mgr)

    tracking = track_mgr.create_tracking()
    track_mgr.update_status(tracking.id, status="completed", progress=1.0)

    result = res_mgr.evaluate_result(tracking_id=tracking.id)

    assert result.id is not None
    assert result.tracking_id == tracking.id
    assert result.result_status == "success"
    assert result.impact == "positive"
    assert "completada exitosamente" in result.summary.lower()


def test_evaluate_result_failed_tracking(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    res_mgr = ExecutionResultManager(db_manager=temp_db, tracking_manager=track_mgr)

    tracking = track_mgr.create_tracking()
    track_mgr.update_status(tracking.id, status="failed", progress=0.4)

    result = res_mgr.evaluate_result(tracking_id=tracking.id)

    assert result.result_status == "failed"
    assert result.impact == "negative"


def test_evaluate_result_running_tracking(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    res_mgr = ExecutionResultManager(db_manager=temp_db, tracking_manager=track_mgr)

    tracking = track_mgr.create_tracking()
    track_mgr.update_status(tracking.id, status="running", progress=0.6)

    result = res_mgr.evaluate_result(tracking_id=tracking.id)

    assert result.result_status == "partial"
    assert result.impact == "neutral"


def test_result_persistence(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    res_mgr = ExecutionResultManager(db_manager=temp_db, tracking_manager=track_mgr)

    tracking = track_mgr.create_tracking()
    track_mgr.update_status(tracking.id, status="completed", progress=1.0)

    result = res_mgr.evaluate_result(tracking_id=tracking.id)

    db_record = temp_db.get_execution_result(result.id)
    assert db_record is not None
    assert db_record["result_status"] == "success"
    assert db_record["impact"] == "positive"
