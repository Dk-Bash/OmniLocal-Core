from datetime import datetime
from typing import Optional, Dict, Any

try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class RuntimeLearningRecord(BaseModel):
    id: Optional[int] = None
    source_execution_id: int = 0
    source_decision_id: int = 0
    learning_type: str = "performance"  # performance, failure_pattern, optimization, recovery
    pattern_detected: str
    confidence: float = 0.0
    impact_prediction: str = ""
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "source_execution_id": self.source_execution_id,
            "source_decision_id": self.source_decision_id,
            "learning_type": self.learning_type,
            "pattern_detected": self.pattern_detected,
            "confidence": self.confidence,
            "impact_prediction": self.impact_prediction,
            "created_at": self.created_at,
        }


class RuntimeAdaptationRecommendation(BaseModel):
    id: Optional[int] = None
    learning_id: int = 0
    target_area: str
    recommended_change: str
    priority: str = "medium"  # low, medium, high, critical
    confidence: float = 0.0
    reasoning: str = ""
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "id": self.id,
            "learning_id": self.learning_id,
            "target_area": self.target_area,
            "recommended_change": self.recommended_change,
            "priority": self.priority,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "created_at": self.created_at,
        }
