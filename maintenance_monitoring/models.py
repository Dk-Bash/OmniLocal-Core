from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class MaintenanceMonitoringReport:
    """Módulo 46: Modelo de Informe de Monitoreo del Ciclo de Mantenimiento."""
    workflow_id: int
    execution_status: str
    health_status: str
    progress: float
    observations: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_health = {"healthy", "warning", "critical"}
        if self.health_status not in allowed_health:
            raise ValueError(
                f"health_status must be one of {allowed_health}, got '{self.health_status}'"
            )

        if not (0.0 <= self.progress <= 1.0):
            raise ValueError(
                f"progress must be a float between 0.0 and 1.0, got '{self.progress}'"
            )
