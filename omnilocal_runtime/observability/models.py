from datetime import datetime
from typing import Optional, Dict, Any

try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class RuntimeMetricReport(BaseModel):
    id: Optional[int] = None
    metric_type: str
    workflow_id: str
    execution_id: int = 0
    value: float = 0.0
    unit: str = ""
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "metric_type": self.metric_type,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "value": self.value,
            "unit": self.unit,
            "created_at": self.created_at,
        }


class RuntimePerformanceReport(BaseModel):
    id: Optional[int] = None
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    most_failed_stage: str = "none"
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "average_execution_time": self.average_execution_time,
            "success_rate": self.success_rate,
            "most_failed_stage": self.most_failed_stage,
            "created_at": self.created_at,
        }
