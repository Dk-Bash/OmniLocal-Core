from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OutcomeEvaluation(BaseModel):
    id: Optional[int] = None
    event_id: int
    result_type: str
    score: float
    summary: str
    created_at: datetime = Field(default_factory=datetime.now)
