from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union


ALLOWED_WORKFLOW_STATUSES = {"pending", "running", "completed", "failed", "blocked"}


@dataclass
class WorkflowDefinition:
    """Define la estructura y metadata de un workflow en OmniLocal Runtime."""
    name: str
    description: str = ""
    stages: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        if self.stages is None:
            self.stages = []


@dataclass
class WorkflowExecution:
    """Representa una instancia de ejecución de un workflow."""
    workflow_id: str
    context_id: int
    current_stage: str = "init"
    status: str = "pending"
    results: List[Dict[str, Any]] = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        if self.status not in ALLOWED_WORKFLOW_STATUSES:
            raise ValueError(
                f"status must be one of {ALLOWED_WORKFLOW_STATUSES}, got '{self.status}'"
            )
        if self.results is None:
            self.results = []
