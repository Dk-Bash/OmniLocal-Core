from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    id: Optional[int] = None
    event_type: str
    source_layer: str
    description: str
    status: str
    created_at: datetime = Field(default_factory=datetime.now)
