from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PrioritizedTask(BaseModel):
    id: Optional[int] = None
    task_type: str
    description: str
    priority_score: float
    priority_level: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)


class PriorityReport(BaseModel):
    total_tasks: int
    critical_tasks: int
    high_tasks: int
    medium_tasks: int
    low_tasks: int
    tasks: List[PrioritizedTask] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
