import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_workflow.manager import MaintenanceWorkflowManager
from maintenance_policy.models import MaintenancePolicyResult
from maintenance_policy.manager import MaintenancePolicyManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_policy_model_validations():
    # Valid
    p = MaintenancePolicyResult(
        workflow_id=1,
        allowed=True,
        risk_level="low",
        reasoning="Policy passed",
    )
    assert p.risk_level == "low"

    # Invalid risk_level
    with pytest.raises(ValueError):
        MaintenancePolicyResult(
            workflow_id=1,
            allowed=True,
            risk_level="ultra_high",
            reasoning="Invalid risk",
        )


def test_policy_evaluations_rules(temp_db):
    wf_mgr = MaintenanceWorkflowManager(db_manager=temp_db)
    policy_mgr = MaintenancePolicyManager(db_manager=temp_db, workflow_manager=wf_mgr)

    # Insert test workflows
    w1_id = temp_db.insert_workflow(1, "adaptive_workflow", '["s1"]', 0, "pending")
    w2_id = temp_db.insert_workflow(2, "standard_workflow", '["s1"]', 0, "pending")
    w3_id = temp_db.insert_workflow(3, "fallback_workflow", '["s1"]', 0, "pending")

    r1 = policy_mgr.evaluate_policy(workflow_id=w1_id)[0]
    assert r1.allowed is True
    assert r1.risk_level == "medium"
    assert len(r1.reasoning) > 0

    r2 = policy_mgr.evaluate_policy(workflow_id=w2_id)[0]
    assert r2.allowed is True
    assert r2.risk_level == "low"

    r3 = policy_mgr.evaluate_policy(workflow_id=w3_id)[0]
    assert r3.allowed is False
    assert r3.risk_level == "high"
    assert "Fallback" in r3.violations
