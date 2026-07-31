from datetime import datetime
from typing import Optional
try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class SimulationResult(BaseModel):
    id: Optional[int] = None
    task_type: str
    simulation_status: str
    expected_impact: str
    details: str
    created_at: datetime = Field(default_factory=datetime.now)
