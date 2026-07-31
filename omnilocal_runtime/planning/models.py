from datetime import datetime
from typing import Optional, Dict, Any, Union, List
import json

try:
    from pydantic import BaseModel, Field
except ImportError:
    from memory.models import BaseModel, Field


class RuntimePlanStep(BaseModel):
    step_number: int = 1
    action: str = ""
    description: str = ""
    expected_result: str = ""
    risk_level: str = "low"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        elif hasattr(self, "dict"):
            return self.dict()
        return {
            "step_number": self.step_number,
            "action": self.action,
            "description": self.description,
            "expected_result": self.expected_result,
            "risk_level": self.risk_level,
        }


class RuntimeExecutionPlan(BaseModel):
    id: Optional[int] = None
    source_decision_id: int = 0
    plan_type: str = "optimization_plan"  # optimization_plan, recovery_plan, investigation_plan, fallback_plan
    steps: str = "[]"  # JSON string con la lista de RuntimePlanStep
    estimated_risk: str = "low"  # low, medium, high, critical
    confidence: float = 0.0
    reasoning: str = ""
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            res = self.model_dump()
        elif hasattr(self, "dict"):
            res = self.dict()
        else:
            res = {
                "id": self.id,
                "source_decision_id": self.source_decision_id,
                "plan_type": self.plan_type,
                "steps": self.steps,
                "estimated_risk": self.estimated_risk,
                "confidence": self.confidence,
                "reasoning": self.reasoning,
                "created_at": self.created_at,
            }
        return res
