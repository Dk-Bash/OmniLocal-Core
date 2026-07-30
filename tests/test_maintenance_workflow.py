import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_workflow.models import MaintenanceWorkflow
from maintenance_workflow.manager import MaintenanceWorkflowManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_workflow_model_validations():
    # Valid model
    wf = MaintenanceWorkflow(
        decision_id=1,
        workflow_type="adaptive_workflow",
        steps=["step1", "step2"],
        current_step=0,
        status="pending",
    )
    assert wf.workflow_type == "adaptive_workflow"

    # Invalid status
    with pytest.raises(ValueError):
        MaintenanceWorkflow(
            decision_id=1,
            workflow_type="adaptive_workflow",
            steps=["step1"],
            status="invalid_status",
        )

    # Invalid workflow_type
    with pytest.raises(ValueError):
        MaintenanceWorkflow(
            decision_id=1,
            workflow_type="invalid_type",
            steps=["step1"],
        )

    # Invalid current_step > steps length
    with pytest.raises(ValueError):
        MaintenanceWorkflow(
            decision_id=1,
            workflow_type="adaptive_workflow",
            steps=["step1"],
            current_step=5,
        )


def test_workflow_manager_lifecycle(temp_db):
    manager = MaintenanceWorkflowManager(db_manager=temp_db)
    workflows = manager.create_workflow()

    assert len(workflows) > 0
    first_wf = workflows[0]
    assert first_wf.id is not None
    assert first_wf.status == "pending"

    # Advance step
    updated = manager.advance_step(first_wf.id)
    assert updated is not None
    assert updated["current_step"] == 1
    assert updated["status"] in {"in_progress", "completed"}

    stored = manager.get_workflow(first_wf.id)
    assert stored is not None
    assert stored["id"] == first_wf.id

    all_wfs = manager.get_workflows()
    assert len(all_wfs) >= len(workflows)
