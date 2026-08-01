from typing import Optional, List, Dict, Any
import json
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.knowledge.manager import RuntimeKnowledgeManager
from omnilocal_runtime.observability.manager import RuntimeObservabilityManager
from omnilocal_runtime.decision_intelligence.manager import KnowledgeAwareDecisionManager
from omnilocal_runtime.planning.models import RuntimeExecutionPlan
from omnilocal_runtime.planning.planner import RuntimePlannerEngine


class RuntimePlanningManager:
    """
    Gestor de Planificación Autónoma para Runtime (Runtime Block 11).
    Consume la capa de Decisiones Aumentadas por Conocimiento (Runtime Block 10),
    el Motor de Conocimiento (Runtime Block 09) y Observabilidad (Runtime Block 06)
    para generar propuestas de planes de ejecución futuros sin alterar nada previamente existente.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        decision_manager: Optional[KnowledgeAwareDecisionManager] = None,
        knowledge_manager: Optional[RuntimeKnowledgeManager] = None,
        obs_manager: Optional[RuntimeObservabilityManager] = None
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.decision_manager = decision_manager or KnowledgeAwareDecisionManager(db_manager=self.db_manager)
        self.knowledge_manager = knowledge_manager or RuntimeKnowledgeManager(db_manager=self.db_manager)
        self.obs_manager = obs_manager or RuntimeObservabilityManager(db_manager=self.db_manager)

    def create_plan(
        self,
        source_decision_id: Optional[int] = None,
        current_metrics: Optional[Dict[str, Any]] = None
    ) -> RuntimeExecutionPlan:
        """
        Genera o recupera una decisión del runtime, consulta el conocimiento asociado,
        construye un plan estructurado con evaluación de riesgo y lo persiste en SQLite.
        """
        # 1. Recuperar o generar la decisión
        decision = None
        if source_decision_id is not None:
            decision = self.decision_manager.get_decision(source_decision_id)

        if decision is None:
            decision_report = self.decision_manager.generate_decision(current_metrics=current_metrics)
            decision = decision_report.to_dict()

        # 2. Recuperar entradas de conocimiento
        knowledge_entries = self.knowledge_manager.get_knowledge_entries()

        # 3. Generar el plan con el Planner Engine
        plan = RuntimePlannerEngine.generate_plan(decision, knowledge_entries)

        # 4. Persistir el plan en SQLite
        inserted_id = self.db_manager.insert_runtime_execution_plan(
            plan_type=plan.plan_type,
            source_decision_id=plan.source_decision_id,
            steps=plan.steps,
            estimated_risk=plan.estimated_risk,
            confidence=plan.confidence,
            reasoning=plan.reasoning
        )
        plan.id = inserted_id

        return plan

    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un plan de ejecución guardado por su ID."""
        return self.db_manager.get_runtime_execution_plan(plan_id)

    def get_plans(self) -> List[Dict[str, Any]]:
        """Obtiene el historial de todos los planes de ejecución autónomos."""
        return self.db_manager.get_runtime_execution_plans()
