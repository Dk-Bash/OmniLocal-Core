from datetime import datetime
from typing import Optional, Dict, Any

try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class RuntimeValidationReport(BaseModel):
    id: Optional[int] = None
    scenario_name: str
    status: str  # 'passed', 'failed', 'partial'
    stages_executed: int = 0
    successful_stages: int = 0
    failed_stages: int = 0
    execution_time: float = 0.0
    summary: str = ""
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "scenario_name": self.scenario_name,
            "status": self.status,
            "stages_executed": self.stages_executed,
            "successful_stages": self.successful_stages,
            "failed_stages": self.failed_stages,
            "execution_time": self.execution_time,
            "summary": self.summary,
            "created_at": self.created_at,
        }
