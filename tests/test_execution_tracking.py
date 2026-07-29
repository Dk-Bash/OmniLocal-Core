import os
import tempfile
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_execution.manager import MaintenanceExecutionManager
from maintenance_validation.manager import ExecutionValidationManager
from maintenance_approval.manager import ExecutionApprovalManager
from maintenance_tracking.models import ExecutionTracking
from maintenance_tracking.manager import ExecutionTrackingManager


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


def test_create_tracking_approved_flow(temp_db):
    plan_mgr = MaintenanceExecutionManager(db_manager=temp_db)
    val_mgr = ExecutionValidationManager(db_manager=temp_db, execution_manager=plan_mgr)
    app_mgr = ExecutionApprovalManager(db_manager=temp_db, validation_manager=val_mgr)
    track_mgr = ExecutionTrackingManager(db_manager=temp_db, approval_manager=app_mgr)

    # 1. Crear plan de ejecución (Default plan -> low risk -> approved)
    plan = plan_mgr.create_execution_plan()
    val_report = val_mgr.validate_plan(plan=plan)
    approval = app_mgr.evaluate_approval(validation_report=val_report)

    assert approval.approved is True

    # 2. Crear tracking
    tracking = track_mgr.create_tracking(approval=approval)

    assert tracking.id is not None
    assert tracking.approval_id == approval.id
    assert tracking.status == "pending"
    assert tracking.progress == 0.0

    # 3. Verificar en DB
    db_record = temp_db.get_execution_tracking(tracking.id)
    assert db_record is not None
    assert db_record["status"] == "pending"


def test_create_tracking_unapproved_flow(temp_db):
    plan_mgr = MaintenanceExecutionManager(db_manager=temp_db)
    val_mgr = ExecutionValidationManager(db_manager=temp_db, execution_manager=plan_mgr)
    app_mgr = ExecutionApprovalManager(db_manager=temp_db, validation_manager=val_mgr)
    track_mgr = ExecutionTrackingManager(db_manager=temp_db, approval_manager=app_mgr)

    # Simular una aprobación rechazada (approved=False)
    app_id = temp_db.insert_execution_approval(
        plan_id=99,
        validation_id=99,
        approval_status="rejected",
        approved=False,
        reason="Rechazado por riesgo excesivo.",
    )
    raw = temp_db.get_execution_approval(app_id)
    from maintenance_approval.models import ExecutionApproval
    approval = ExecutionApproval(
        id=raw["id"],
        plan_id=raw["plan_id"],
        validation_id=raw["validation_id"],
        approval_status=raw["approval_status"],
        approved=raw["approved"],
        reason=raw["reason"],
        created_at=raw["created_at"],
    )

    assert approval.approved is False

    tracking = track_mgr.create_tracking(approval=approval)

    assert tracking.status == "cancelled"
    assert tracking.progress == 0.0


def test_update_tracking_status_and_progress(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    tracking = track_mgr.create_tracking()

    # Actualizar a running
    updated1 = track_mgr.update_status(
        tracking_id=tracking.id,
        status="running",
        progress=0.5,
        message="Ejecución al 50%"
    )
    assert updated1.status == "running"
    assert updated1.progress == 0.5

    # Actualizar a completed
    updated2 = track_mgr.update_status(
        tracking_id=tracking.id,
        status="completed",
        progress=1.0,
        message="Ejecución finalizada con éxito"
    )
    assert updated2.status == "completed"
    assert updated2.progress == 1.0


def test_invalid_progress_raises_error(temp_db):
    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    tracking = track_mgr.create_tracking()

    with pytest.raises(ValueError):
        track_mgr.update_status(tracking_id=tracking.id, status="running", progress=1.5)

    with pytest.raises(ValueError):
        track_mgr.update_status(tracking_id=tracking.id, status="running", progress=-0.1)


def test_no_side_effects_on_memories(temp_db):
    # Asegurar que el conteo de memorias no cambie al usar tracking
    initial_memories = temp_db.count_memories()

    track_mgr = ExecutionTrackingManager(db_manager=temp_db)
    t = track_mgr.create_tracking()
    track_mgr.update_status(t.id, "running", 0.3)
    track_mgr.update_status(t.id, "completed", 1.0)

    assert temp_db.count_memories() == initial_memories
