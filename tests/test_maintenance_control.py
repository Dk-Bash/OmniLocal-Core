import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_control.models import ControlOptimizationReport
from maintenance_control.manager import AutonomousControlManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_control.db"
    manager = SQLiteManager(db_path=str(db_file))
    manager.create_tables()
    yield manager
    manager.close()


def test_control_model_validations():
    report = ControlOptimizationReport(
        compliance_id=1,
        optimization_status="optimized",
        improvement_area="Eficiencia",
        confidence=0.95,
        recommendation="Avanzar",
    )
    assert report.optimization_status == "optimized"
    assert report.confidence == 0.95

    with pytest.raises(ValueError):
        ControlOptimizationReport(
            compliance_id=1,
            optimization_status="invalid",
            improvement_area="Test",
            confidence=0.5,
            recommendation="Test",
        )

    with pytest.raises(ValueError):
        ControlOptimizationReport(
            compliance_id=1,
            optimization_status="optimized",
            improvement_area="Test",
            confidence=2.0,
            recommendation="Test",
        )


def test_control_manager_optimization_rules(temp_db):
    # Insertar informes de cumplimiento simulados
    temp_db.insert_compliance_report(1, True, "Ninguna", 1.0, "Recomendación A")
    temp_db.insert_compliance_report(2, False, "Revisión", 0.5, "Recomendación B")
    temp_db.insert_compliance_report(3, False, "Violación", 0.0, "Recomendación C")

    ctrl_manager = AutonomousControlManager(db_manager=temp_db)
    opts = ctrl_manager.optimize_control()

    assert len(opts) == 3

    opt_map = {o.compliance_id: o for o in opts}

    # compliance 1 (score 1.0 >= 0.9) -> optimized
    assert opt_map[1].optimization_status == "optimized"
    assert len(opt_map[1].improvement_area) > 0
    assert len(opt_map[1].recommendation) > 0

    # compliance 2 (score 0.5 -> 0.5 <= score < 0.9) -> stable
    assert opt_map[2].optimization_status == "stable"
    assert len(opt_map[2].improvement_area) > 0
    assert len(opt_map[2].recommendation) > 0

    # compliance 3 (score 0.0 -> score < 0.5) -> needs_improvement
    assert opt_map[3].optimization_status == "needs_improvement"
    assert len(opt_map[3].improvement_area) > 0
    assert len(opt_map[3].recommendation) > 0


def test_control_integrity_no_side_effects(temp_db):
    temp_db.insert_compliance_report(1, True, "Ninguna", 1.0, "Rec")
    comp_before = temp_db.get_compliance_reports()

    ctrl_manager = AutonomousControlManager(db_manager=temp_db)
    ctrl_manager.optimize_control()

    comp_after = temp_db.get_compliance_reports()
    assert len(comp_before) == len(comp_after)
    assert comp_before == comp_after
