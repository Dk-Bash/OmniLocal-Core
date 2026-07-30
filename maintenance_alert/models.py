from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class MaintenanceAlert:
    """Módulo 47: Modelo de Alerta Inteligente de Mantenimiento."""
    monitoring_id: int
    alert_type: str
    severity: str
    message: str
    recommended_action: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_types = {"information", "warning", "failure"}
        if self.alert_type not in allowed_types:
            raise ValueError(
                f"alert_type must be one of {allowed_types}, got '{self.alert_type}'"
            )

        allowed_severities = {"low", "medium", "high", "critical"}
        if self.severity not in allowed_severities:
            raise ValueError(
                f"severity must be one of {allowed_severities}, got '{self.severity}'"
            )
