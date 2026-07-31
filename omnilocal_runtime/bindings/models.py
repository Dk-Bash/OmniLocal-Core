from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union


@dataclass
class CapabilityBindingResult:
    """
    Representa el resultado de la ejecución de una etapa de workflow
    conectada a una capacidad real (manager).
    """
    stage_name: str
    manager_name: str
    success: bool = True
    summary: str = ""
    data: Optional[Union[Dict[str, Any], list, str]] = field(default_factory=dict)
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a un diccionario serializable."""
        return {
            "id": self.id,
            "stage_name": self.stage_name,
            "manager_name": self.manager_name,
            "success": self.success,
            "summary": self.summary,
            "data": self.data,
            "created_at": self.created_at,
        }
