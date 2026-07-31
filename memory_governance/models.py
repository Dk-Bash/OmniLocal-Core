from datetime import datetime
from typing import Optional
try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class MaintenanceApproval(BaseModel):
    id: Optional[int] = None
    task_type: str
    risk_level: str
    approval_status: str
    reason: str
    created_at: datetime = Field(default_factory=datetime.now)
