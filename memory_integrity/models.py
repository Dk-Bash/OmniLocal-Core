from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MemoryIssue(BaseModel):
    id: Optional[int] = None
    memory_id: Optional[int] = None
    issue_type: str
    description: str
    severity: str
    created_at: datetime = Field(default_factory=datetime.now)


class IntegrityReport(BaseModel):
    total_checked: int
    issues_found: int
    issues: List[MemoryIssue]
    created_at: datetime = Field(default_factory=datetime.now)
