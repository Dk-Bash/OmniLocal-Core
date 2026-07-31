from datetime import datetime
from typing import Optional, Dict, Any, Union, List
import json

try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class KnowledgeAwareDecisionReport(BaseModel):
    id: Optional[int] = None
    source_knowledge_ids: str = ""  # p.ej. "1,2,5" o JSON string
    decision_type: str = "continue"  # continue, optimize, investigate, fallback
    confidence: float = 0.0
    supporting_patterns: str = ""  # p.ej. "validation_instability, performance_drop"
    recommended_action: str = ""
    reasoning: str = ""
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "source_knowledge_ids": self.source_knowledge_ids,
            "decision_type": self.decision_type,
            "confidence": self.confidence,
            "supporting_patterns": self.supporting_patterns,
            "recommended_action": self.recommended_action,
            "reasoning": self.reasoning,
            "created_at": self.created_at,
        }


class DecisionKnowledgeContext(BaseModel):
    id: Optional[int] = None
    query: str = "general_metrics_context"
    matched_patterns: str = ""  # JSON string o lista serializada
    relevance_score: float = 0.0
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "query": self.query,
            "matched_patterns": self.matched_patterns,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at,
        }
