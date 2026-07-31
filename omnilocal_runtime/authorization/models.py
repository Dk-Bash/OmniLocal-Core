import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class RuntimeAuthorizationCondition:
    condition_name: str
    condition_status: str  # "passed", "warning", "failed"
    description: str = ""
    severity: str = "info"  # "info", "medium", "critical", "high", "low"
    id: Optional[int] = None
    authorization_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "authorization_id": self.authorization_id,
            "condition_name": self.condition_name,
            "condition_status": self.condition_status,
            "description": self.description,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeAuthorizationCondition":
        return cls(
            id=data.get("id"),
            authorization_id=data.get("authorization_id"),
            condition_name=data.get("condition_name", "unknown_condition"),
            condition_status=data.get("condition_status", "passed"),
            description=data.get("description", ""),
            severity=data.get("severity", "info"),
        )


@dataclass
class RuntimeExecutionAuthorization:
    plan_id: int
    validation_id: int
    authorization_status: str  # "authorized", "authorized_with_conditions", "rejected"
    authorization_level: str = "normal"  # "high_trust", "normal", "restricted", "blocked"
    approved_conditions: List[str] = field(default_factory=list)
    rejected_conditions: List[str] = field(default_factory=list)
    reasoning: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None
    conditions: List[RuntimeAuthorizationCondition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "validation_id": self.validation_id,
            "authorization_status": self.authorization_status,
            "authorization_level": self.authorization_level,
            "approved_conditions": self.approved_conditions if isinstance(self.approved_conditions, list) else json.loads(self.approved_conditions or "[]"),
            "rejected_conditions": self.rejected_conditions if isinstance(self.rejected_conditions, list) else json.loads(self.rejected_conditions or "[]"),
            "reasoning": self.reasoning,
            "created_at": self.created_at or datetime.now().isoformat(),
            "conditions": [c.to_dict() for c in self.conditions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeExecutionAuthorization":
        app_conds = data.get("approved_conditions", [])
        if isinstance(app_conds, str):
            try:
                app_conds = json.loads(app_conds)
            except Exception:
                app_conds = []

        rej_conds = data.get("rejected_conditions", [])
        if isinstance(rej_conds, str):
            try:
                rej_conds = json.loads(rej_conds)
            except Exception:
                rej_conds = []

        raw_conditions = data.get("conditions", [])
        conditions_list = []
        for c in raw_conditions:
            if isinstance(c, dict):
                conditions_list.append(RuntimeAuthorizationCondition.from_dict(c))

        return cls(
            id=data.get("id"),
            plan_id=data.get("plan_id", 0),
            validation_id=data.get("validation_id", 0),
            authorization_status=data.get("authorization_status", "rejected"),
            authorization_level=data.get("authorization_level", "normal"),
            approved_conditions=app_conds,
            rejected_conditions=rej_conds,
            reasoning=data.get("reasoning", ""),
            created_at=data.get("created_at"),
            conditions=conditions_list,
        )
