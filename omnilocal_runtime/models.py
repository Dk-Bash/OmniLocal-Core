from dataclasses import dataclass, field
from typing import Optional, List, Any


@dataclass
class RuntimeResult:
    """Resultado consolidado de la ejecución de un pipeline o proceso en el Runtime."""
    context_id: int
    success: bool
    summary: str
    executed_stages: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        if self.executed_stages is None:
            self.executed_stages = []
        if self.errors is None:
            self.errors = []
