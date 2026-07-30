import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_compliance.models import ComplianceReport
from maintenance_compliance.manager import MaintenanceComplianceManager
from maintenance_governance.manager import MaintenanceGovernanceManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_compliance.db"
    manager = SQLiteManager(db_path=str(db_file))
    manager.create_tables()
    yield manager
    manager.close()


def test_compliance_model_validations():
    report = ComplianceReport(
        governance_id=1,
        compliant=True,
        violations="Ninguna",
        compliance_score=1.0,
        recommendation="Seguir con el plan",
    )
    assert report.compliant is True
    assert report.compliance_score == 1.0

    with pytest.raises(ValueError):
        ComplianceReport(
            governance_id=1,
            compliant=True,
            violations="Test",
            compliance_score=1.5,
            recommendation="Test",
        )


def test_compliance_manager_validation_rules(temp_db):
    # Insertar evaluaciones de gobernanza simuladas
    temp_db.insert_governance_evaluation(1, "approved", "low", "Rules 1", "Reason 1")
    temp_db.insert_governance_evaluation(2, "review_required", "medium", "Rules 2", "Reason 2")
    temp_db.insert_governance_evaluation(3, "blocked", "critical", "Rules 3", "Reason 3")

    comp_manager = MaintenanceComplianceManager(db_manager=temp_db)
    reports = comp_manager.validate_compliance()

    assert len(reports) == 3

    rep_map = {r.governance_id: r for r in reports}

    # governance 1 ('approved') -> compliant=True, score=1.0
    assert rep_map[1].compliant is True
    assert rep_map[1].compliance_score == 1.0
    assert len(rep_map[1].recommendation) > 0

    # governance 2 ('review_required') -> compliant=False, score=0.5
    assert rep_map[2].compliant is False
    assert rep_map[2].compliance_score == 0.5
    assert len(rep_map[2].recommendation) > 0

    # governance 3 ('blocked') -> compliant=False, score=0.0
    assert rep_map[3].compliant is False
    assert rep_map[3].compliance_score == 0.0
    assert len(rep_map[3].recommendation) > 0


def test_compliance_integrity_no_side_effects(temp_db):
    temp_db.insert_governance_evaluation(1, "approved", "low", "Rules", "Reason")
    gov_before = temp_db.get_governance_evaluations()

    comp_manager = MaintenanceComplianceManager(db_manager=temp_db)
    comp_manager.validate_compliance()

    gov_after = temp_db.get_governance_evaluations()
    assert len(gov_before) == len(gov_after)
    assert gov_before == gov_after
