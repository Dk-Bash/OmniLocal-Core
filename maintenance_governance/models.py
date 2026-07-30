from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class GovernanceEvaluation:
    """Módulo 49: Modelo de Evaluación de Gobernanza de Mantenimiento."""
    decision_id: int
    governance_status: str
    risk_level: str
    rules_checked: str
    reasoning: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_statuses = {"approved", "review_required", "blocked"}
        if self.governance_status not in allowed_statuses:
            raise ValueError(
                f"governance_status must be one of {allowed_statuses}, got '{self.governance_status}'"
            )

        allowed_risks = {"low", "medium", "high", "critical"}
        if self.risk_level not in allowed_risks:
            raise ValueError(
                f"risk_level must be one of {allowed_risks}, got '{self.risk_level}'"
            )
