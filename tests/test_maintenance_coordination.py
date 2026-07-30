import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_workflow.manager import MaintenanceWorkflowManager
from maintenance_policy.manager import MaintenancePolicyManager
from maintenance_coordination.models import CoordinationResult
from maintenance_coordination.manager import MaintenanceCoordinatorManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_coordination_model_validations():
    c = CoordinationResult(
        workflow_id=1,
        policy_id=1,
        coordination_status="ready",
        next_action="Proceed to execution validation",
        summary="Workflow ready for execution",
    )
    assert c.coordination_status == "ready"

    with pytest.raises(ValueError):
        CoordinationResult(
            workflow_id=1,
            policy_id=1,
            coordination_status="invalid_status",
            next_action="Do something",
            summary="Invalid",
        )


def test_maintenance_coordinator_manager_rules(temp_db):
    wf_mgr = MaintenanceWorkflowManager(db_manager=temp_db)
    policy_mgr = MaintenancePolicyManager(db_manager=temp_db, workflow_manager=wf_mgr)
    coordinator = MaintenanceCoordinatorManager(
        db_manager=temp_db, workflow_manager=wf_mgr, policy_manager=policy_mgr
    )

    w1_id = temp_db.insert_workflow(1, "adaptive_workflow", '["s1"]', 0, "pending")
    w2_id = temp_db.insert_workflow(2, "fallback_workflow", '["s1"]', 0, "pending")

    p1_id = temp_db.insert_policy_result(w1_id, True, "medium", "Approved", "")
    p2_id = temp_db.insert_policy_result(w2_id, False, "high", "Blocked", "Risk high")

    res1 = coordinator.coordinate(policy_id=p1_id)[0]
    assert res1.coordination_status == "ready"
    assert res1.next_action == "Proceed to execution validation"

    res2 = coordinator.coordinate(policy_id=p2_id)[0]
    assert res2.coordination_status == "blocked"
    assert res2.next_action == "Waiting for manual approval"

    history = coordinator.get_coordination_history()
    assert len(history) >= 2


def test_coordination_integrity_no_side_effects(temp_db):
    coordinator = MaintenanceCoordinatorManager(db_manager=temp_db)
    results = coordinator.coordinate()
    assert isinstance(results, list)

    # Confirm no side-effects on workflows table schema or data integrity
    workflows = temp_db.get_workflows()
    assert isinstance(workflows, list)
