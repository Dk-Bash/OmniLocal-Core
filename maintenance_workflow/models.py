from dataclasses import dataclass
import json
from typing import Optional, Any, List


@dataclass
class MaintenanceWorkflow:
    """Módulo 43: Modelo de Flujo de Trabajo de Mantenimiento."""
    decision_id: int
    workflow_type: str
    steps: List[str]
    current_step: int = 0
    status: str = "pending"
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_statuses = {"pending", "in_progress", "completed", "blocked"}
        if self.status not in allowed_statuses:
            raise ValueError(
                f"status must be one of {allowed_statuses}, got '{self.status}'"
            )

        allowed_types = {"adaptive_workflow", "standard_workflow", "fallback_workflow"}
        if self.workflow_type not in allowed_types:
            raise ValueError(
                f"workflow_type must be one of {allowed_types}, got '{self.workflow_type}'"
            )

        if isinstance(self.steps, str):
            try:
                self.steps = json.loads(self.steps)
            except Exception:
                self.steps = [s.strip() for s in self.steps.split(",") if s.strip()]

        if not isinstance(self.steps, list):
            raise ValueError("steps must be a list or a valid JSON list string")

        if int(self.current_step) < 0:
            raise ValueError(f"current_step cannot be negative, got {self.current_step}")

        if int(self.current_step) > len(self.steps):
            raise ValueError(
                f"current_step ({self.current_step}) cannot exceed total steps count ({len(self.steps)})"
            )
