from dataclasses import dataclass, field
from typing import Optional, Dict, Any


ALLOWED_STATUSES = {"initialized", "running", "completed", "failed", "blocked"}


@dataclass
class RuntimeContext:
    """Representa el estado de una ejecución completa en el Runtime de OmniLocal."""
    operation_type: str
    current_stage: str = "init"
    status: str = "initialized"
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(
                f"status must be one of {ALLOWED_STATUSES}, got '{self.status}'"
            )
        if self.metadata is None:
            self.metadata = {}
