from typing import Optional, List, Dict, Any
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.knowledge.manager import RuntimeKnowledgeManager
from omnilocal_runtime.observability.manager import RuntimeObservabilityManager
from omnilocal_runtime.validation.manager import RuntimeValidationManager
from omnilocal_runtime.decision_intelligence.models import KnowledgeAwareDecisionReport
from omnilocal_runtime.decision_intelligence.knowledge_context import RuntimeKnowledgeContextBuilder
from omnilocal_runtime.decision_intelligence.reasoning import KnowledgeAwareReasoningEngine


class KnowledgeAwareDecisionManager:
    """
    Gestor de Toma de Decisiones Aumentadas por Conocimiento (Runtime Block 10).
    Consulta el conocimiento histórico consolidado (Runtime Block 09), evalúa métricas actuales
    y validaciones para generar decisiones con contexto sin modificar flujos o datos históricos.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        knowledge_manager: Optional[RuntimeKnowledgeManager] = None,
        obs_manager: Optional[RuntimeObservabilityManager] = None,
        val_manager: Optional[RuntimeValidationManager] = None
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.knowledge_manager = knowledge_manager or RuntimeKnowledgeManager(db_manager=self.db_manager)
        self.obs_manager = obs_manager or RuntimeObservabilityManager(db_manager=self.db_manager)
        self.val_manager = val_manager or RuntimeValidationManager(db_manager=self.db_manager)

    def generate_decision(
        self,
        current_metrics: Optional[Dict[str, Any]] = None,
        validation_reports: Optional[List[Dict[str, Any]]] = None
    ) -> KnowledgeAwareDecisionReport:
        """
        Obtiene métricas runtime, consulta el conocimiento histórico, genera el contexto
        y elabora un informe de decisión basada en conocimiento, persistiéndolo en SQLite.
        """
        if current_metrics is None:
            raw_metrics = self.obs_manager.get_telemetry_metrics()
            current_metrics = {
                "error_rate": raw_metrics.get("error_rate", 0.0),
                "avg_latency": raw_metrics.get("avg_latency_ms", 120.0),
                "cpu_usage": raw_metrics.get("cpu_usage", 25.0),
                "memory_usage": raw_metrics.get("memory_usage", 40.0),
            }

        if validation_reports is None:
            raw_reports = self.val_manager.get_reports()
            validation_reports = []
            for r in raw_reports:
                status = r.get("status", "failed")
                validation_reports.append({
                    "success": (status == "success" or status == "PASSED"),
                    "details": r.get("summary", "")
                })

        knowledge_entries = self.knowledge_manager.get_knowledge_entries()

        if not knowledge_entries:
            # Consolidar conocimiento si aún no existe
            self.knowledge_manager.consolidate_knowledge()
            knowledge_entries = self.knowledge_manager.get_knowledge_entries()

        # Construir contexto de conocimiento
        knowledge_context = RuntimeKnowledgeContextBuilder.build_context(knowledge_entries, current_metrics)

        # Evaluar decisión con motor de razonamiento
        decision_report = KnowledgeAwareReasoningEngine.evaluate_with_context(
            current_metrics=current_metrics,
            validation_reports=validation_reports,
            knowledge_context=knowledge_context
        )

        # Persistir decisión en SQLite
        inserted_id = self.db_manager.insert_knowledge_decision(
            decision_type=decision_report.decision_type,
            source_knowledge_ids=decision_report.source_knowledge_ids,
            confidence=decision_report.confidence,
            supporting_patterns=decision_report.supporting_patterns,
            recommended_action=decision_report.recommended_action,
            reasoning=decision_report.reasoning
        )
        decision_report.id = inserted_id

        return decision_report

    def get_decision(self, decision_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un informe de decisión guardado por su ID."""
        return self.db_manager.get_knowledge_decision(decision_id)

    def get_decisions(self) -> List[Dict[str, Any]]:
        """Obtiene el historial de todas las decisiones aumentadas por conocimiento."""
        return self.db_manager.get_knowledge_decisions()
