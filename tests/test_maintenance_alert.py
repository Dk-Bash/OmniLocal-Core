import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_monitoring.manager import MaintenanceMonitoringManager
from maintenance_alert.models import MaintenanceAlert
from maintenance_alert.manager import MaintenanceAlertManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_alert_model_validations():
    a = MaintenanceAlert(
        monitoring_id=1,
        alert_type="information",
        severity="low",
        message="System ok",
        recommended_action="Keep watching",
    )
    assert a.alert_type == "information"

    # Invalid alert type
    with pytest.raises(ValueError):
        MaintenanceAlert(
            monitoring_id=1,
            alert_type="emergency",
            severity="low",
            message="Invalid",
            recommended_action="None",
        )

    # Invalid severity
    with pytest.raises(ValueError):
        MaintenanceAlert(
            monitoring_id=1,
            alert_type="warning",
            severity="extreme",
            message="Invalid",
            recommended_action="None",
        )


def test_alert_generation_rules(temp_db):
    mon_mgr = MaintenanceMonitoringManager(db_manager=temp_db)
    alert_mgr = MaintenanceAlertManager(db_manager=temp_db, monitoring_manager=mon_mgr)

    # Insert test monitoring reports
    m1_id = temp_db.insert_monitoring_report(1, "completed", "healthy", 1.0, "OK")
    m2_id = temp_db.insert_monitoring_report(2, "running", "warning", 0.5, "Running")
    m3_id = temp_db.insert_monitoring_report(3, "failed", "critical", 0.0, "Failed")

    a1 = alert_mgr.generate_alerts(monitoring_id=m1_id)[0]
    assert a1.alert_type == "information"
    assert a1.severity == "low"
    assert len(a1.recommended_action) > 0

    a2 = alert_mgr.generate_alerts(monitoring_id=m2_id)[0]
    assert a2.alert_type == "warning"
    assert a2.severity == "medium"
    assert len(a2.recommended_action) > 0

    a3 = alert_mgr.generate_alerts(monitoring_id=m3_id)[0]
    assert a3.alert_type == "failure"
    assert a3.severity == "critical"
    assert len(a3.recommended_action) > 0

    all_alerts = alert_mgr.get_alerts()
    assert len(all_alerts) == 3


def test_alert_integrity_no_side_effects(temp_db):
    alert_mgr = MaintenanceAlertManager(db_manager=temp_db)
    alerts = alert_mgr.generate_alerts()
    assert isinstance(alerts, list)

    workflows = temp_db.get_workflows()
    assert isinstance(workflows, list)
