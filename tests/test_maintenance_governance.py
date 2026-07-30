import os
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_governance.models import GovernanceEvaluation
from maintenance_governance.manager import MaintenanceGovernanceManager
from maintenance_supervision.manager import MaintenanceSupervisorManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_governance.db"
    manager = SQLiteManager(db_path=str(db_file))
    manager.create_tables()
    yield manager
    manager.close()


def test_governance_model_validations():
    eval_model = GovernanceEvaluation(
        decision_id=1,
        governance_status="approved",
        risk_level="low",
        rules_checked="Reglas de prueba",
        reasoning="Explicación",
    )
    assert eval_model.governance_status == "approved"
    assert eval_model.risk_level == "low"

    with pytest.raises(ValueError):
        GovernanceEvaluation(
            decision_id=1,
            governance_status="invalid_status",
            risk_level="low",
            rules_checked="Test",
            reasoning="Test",
        )

    with pytest.raises(ValueError):
        GovernanceEvaluation(
            decision_id=1,
            governance_status="approved",
            risk_level="extreme",
            rules_checked="Test",
            reasoning="Test",
        )


def test_governance_manager_evaluation_rules(temp_db):
    # Insertar decisiones simuladas de supervisión
    temp_db.insert_supervisor_decision(1, "continue", "Acción A", "low", "Continuar")
    temp_db.insert_supervisor_decision(2, "review", "Acción B", "medium", "Revisar")
    temp_db.insert_supervisor_decision(3, "stop", "Acción C", "high", "Detener")

    gov_manager = MaintenanceGovernanceManager(db_manager=temp_db)
    evals = gov_manager.evaluate_governance()

    assert len(evals) == 3

    # Mapear por decision_id
    eval_map = {e.decision_id: e for e in evals}

    # decision 1 ('continue') -> approved, low
    assert eval_map[1].governance_status == "approved"
    assert eval_map[1].risk_level == "low"
    assert "Gobernanza Aprobada" in eval_map[1].rules_checked

    # decision 2 ('review') -> review_required, medium
    assert eval_map[2].governance_status == "review_required"
    assert eval_map[2].risk_level == "medium"
    assert "Gobernanza Bajo Revisión" in eval_map[2].rules_checked

    # decision 3 ('stop') -> blocked, critical
    assert eval_map[3].governance_status == "blocked"
    assert eval_map[3].risk_level == "critical"
    assert "Gobernanza Bloqueada" in eval_map[3].rules_checked


def test_governance_integrity_no_side_effects(temp_db):
    temp_db.insert_supervisor_decision(1, "continue", "Acción", "low", "Razón")
    decisions_before = temp_db.get_supervisor_decisions()

    gov_manager = MaintenanceGovernanceManager(db_manager=temp_db)
    gov_manager.evaluate_governance()

    decisions_after = temp_db.get_supervisor_decisions()
    assert len(decisions_before) == len(decisions_after)
    assert decisions_before == decisions_after
