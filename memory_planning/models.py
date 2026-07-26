from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MaintenanceTask(BaseModel):
    id: Optional[int] = None
    task_type: str
    description: str
    priority: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)


class MaintenancePlan(BaseModel):
    id: Optional[int] = None
    total_tasks: int
    high_priority_tasks: int
    medium_priority_tasks: int
    tasks: List[MaintenanceTask] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
