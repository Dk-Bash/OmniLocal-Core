from datetime import datetime
from typing import Optional
try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class MaintenanceRecommendation(BaseModel):
    id: Optional[int] = None
    issue_type: str
    recommendation: str
    priority: str
    created_at: datetime = Field(default_factory=datetime.now)
