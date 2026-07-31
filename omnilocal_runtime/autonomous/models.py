from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class AutonomousExecutionCycle:
    """
    Representa un ciclo de ejecución autónoma completo en OmniLocal Runtime (Runtime Block 04).
    Trazabiliza el progreso, las etapas completadas/fallidas y el success rate del workflow.
    """
    workflow_id: str = "memory_optimization"
    completed_stages: int = 0
    failed_stages: int = 0
    total_stages: int = 9
    success_rate: float = 0.0
    status: str = "running"  # "running", "completed", "failed", "partial"
    id: Optional[int] = None
    created_at: Optional[Any] = None
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el ciclo autónomo a un diccionario serializable."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "completed_stages": self.completed_stages,
            "failed_stages": self.failed_stages,
            "total_stages": self.total_stages,
            "success_rate": self.success_rate,
            "created_at": self.created_at,
            "details": self.details,
        }

    def dict(self) -> Dict[str, Any]:
        return self.to_dict()

    def model_dump(self) -> Dict[str, Any]:
        return self.to_dict()
