import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_workflow.manager import MaintenanceWorkflowManager
from maintenance_tracking.manager import ExecutionTrackingManager
from maintenance_monitoring.models import MaintenanceMonitoringReport
from maintenance_monitoring.manager import MaintenanceMonitoringManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_monitoring_model_validations():
    rep = MaintenanceMonitoringReport(
        workflow_id=1,
        execution_status="completed",
        health_status="healthy",
        progress=1.0,
        observations="OK",
    )
    assert rep.health_status == "healthy"
    assert rep.progress == 1.0

    # Invalid health status
    with pytest.raises(ValueError):
        MaintenanceMonitoringReport(
            workflow_id=1,
            execution_status="completed",
            health_status="super_healthy",
            progress=1.0,
            observations="Invalid",
        )

    # Invalid progress
    with pytest.raises(ValueError):
        MaintenanceMonitoringReport(
            workflow_id=1,
            execution_status="running",
            health_status="warning",
            progress=1.5,
            observations="Invalid progress",
        )


def test_monitoring_manager_report_generation(temp_db):
    wf_mgr = MaintenanceWorkflowManager(db_manager=temp_db)
    tr_mgr = ExecutionTrackingManager(db_manager=temp_db)
    mon_mgr = MaintenanceMonitoringManager(
        db_manager=temp_db, workflow_manager=wf_mgr, tracking_manager=tr_mgr
    )

    w1_id = temp_db.insert_workflow(1, "adaptive_workflow", '["s1"]', 0, "completed")
    w2_id = temp_db.insert_workflow(2, "standard_workflow", '["s1"]', 0, "running")
    w3_id = temp_db.insert_workflow(3, "fallback_workflow", '["s1"]', 0, "failed")

    r1 = mon_mgr.generate_monitoring_report(workflow_id=w1_id)[0]
    assert r1.health_status == "healthy"
    assert r1.progress == 1.0

    r2 = mon_mgr.generate_monitoring_report(workflow_id=w2_id)[0]
    assert r2.health_status == "warning"
    assert r2.progress == 0.5

    r3 = mon_mgr.generate_monitoring_report(workflow_id=w3_id)[0]
    assert r3.health_status == "critical"
    assert r3.progress == 0.0

    reports = mon_mgr.get_monitoring_reports()
    assert len(reports) == 3


def test_monitoring_integrity_no_side_effects(temp_db):
    mon_mgr = MaintenanceMonitoringManager(db_manager=temp_db)
    reports = mon_mgr.generate_monitoring_report(execution_status="completed")
    assert len(reports) == 1

    workflows = temp_db.get_workflows()
    assert isinstance(workflows, list)
