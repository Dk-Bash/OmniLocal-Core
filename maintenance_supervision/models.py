from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class SupervisorDecision:
    """Módulo 48: Modelo de Decisión de Supervisión Lógica de Mantenimiento."""
    alert_id: int
    decision_type: str
    recommended_action: str
    priority: str
    reasoning: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_types = {"continue", "review", "stop"}
        if self.decision_type not in allowed_types:
            raise ValueError(
                f"decision_type must be one of {allowed_types}, got '{self.decision_type}'"
            )

        allowed_priorities = {"low", "medium", "high", "critical"}
        if self.priority not in allowed_priorities:
            raise ValueError(
                f"priority must be one of {allowed_priorities}, got '{self.priority}'"
            )
