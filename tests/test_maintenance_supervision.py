import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_alert.manager import MaintenanceAlertManager
from maintenance_supervision.models import SupervisorDecision
from maintenance_supervision.manager import MaintenanceSupervisorManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_supervisor_model_validations():
    d = SupervisorDecision(
        alert_id=1,
        decision_type="continue",
        recommended_action="Keep running",
        priority="low",
        reasoning="All green",
    )
    assert d.decision_type == "continue"

    # Invalid decision_type
    with pytest.raises(ValueError):
        SupervisorDecision(
            alert_id=1,
            decision_type="ignore_everything",
            recommended_action="Do nothing",
            priority="low",
            reasoning="Invalid",
        )

    # Invalid priority
    with pytest.raises(ValueError):
        SupervisorDecision(
            alert_id=1,
            decision_type="review",
            recommended_action="Check logs",
            priority="ultra_high",
            reasoning="Invalid",
        )


def test_supervisor_manager_rules(temp_db):
    alert_mgr = MaintenanceAlertManager(db_manager=temp_db)
    sup_mgr = MaintenanceSupervisorManager(db_manager=temp_db, alert_manager=alert_mgr)

    # Insert test alerts
    m_id = temp_db.insert_monitoring_report(1, "completed", "healthy", 1.0, "OK")
    a1_id = temp_db.insert_alert(m_id, "information", "low", "System OK", "Continue")
    a2_id = temp_db.insert_alert(m_id, "warning", "medium", "System Slow", "Check logs")
    a3_id = temp_db.insert_alert(m_id, "failure", "critical", "System Crash", "Stop immediately")

    d1 = sup_mgr.generate_supervisor_decision(alert_id=a1_id)[0]
    assert d1.decision_type == "continue"
    assert d1.priority == "low"
    assert len(d1.reasoning) > 0

    d2 = sup_mgr.generate_supervisor_decision(alert_id=a2_id)[0]
    assert d2.decision_type == "review"
    assert d2.priority == "medium"
    assert len(d2.reasoning) > 0

    d3 = sup_mgr.generate_supervisor_decision(alert_id=a3_id)[0]
    assert d3.decision_type == "stop"
    assert d3.priority == "critical"
    assert len(d3.reasoning) > 0

    all_decisions = sup_mgr.get_supervisor_decisions()
    assert len(all_decisions) == 3


def test_supervisor_integrity_no_side_effects(temp_db):
    sup_mgr = MaintenanceSupervisorManager(db_manager=temp_db)
    decisions = sup_mgr.generate_supervisor_decision()
    assert isinstance(decisions, list)

    workflows = temp_db.get_workflows()
    assert isinstance(workflows, list)
