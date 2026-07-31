from datetime import datetime
from typing import Optional, Dict, Any

try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class RuntimeKnowledgeEntry(BaseModel):
    id: Optional[int] = None
    knowledge_type: str = "performance_pattern"  # performance_pattern, failure_pattern, optimization_pattern, recovery_pattern
    source_learning_id: int = 0
    pattern: str
    description: str = ""
    confidence: float = 0.0
    usage_count: int = 0
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "knowledge_type": self.knowledge_type,
            "source_learning_id": self.source_learning_id,
            "pattern": self.pattern,
            "description": self.description,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
        }


class RuntimeKnowledgeQuery(BaseModel):
    id: Optional[int] = None
    query_type: str = "pattern_search"
    query_value: str
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "query_type": self.query_type,
            "query_value": self.query_value,
            "created_at": self.created_at,
        }
