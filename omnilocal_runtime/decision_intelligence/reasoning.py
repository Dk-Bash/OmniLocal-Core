from typing import Dict, Any, List, Union
import json
from omnilocal_runtime.decision_intelligence.models import KnowledgeAwareDecisionReport, DecisionKnowledgeContext


class KnowledgeAwareReasoningEngine:
    """
    Motor de Razonamiento Aumentado por Conocimiento (Runtime Block 10).
    Combina métricas runtime actuales, informes de validación y conocimiento histórico
    para tomar decisiones informadas (continue, optimize, investigate, fallback).
    """

    @staticmethod
    def calculate_decision_confidence(
        metrics_confidence: float,
        knowledge_relevance: float,
        pattern_count: int
    ) -> float:
        """
        Calcula la confianza global de la decisión considerando métricas actuales y relevancia del conocimiento.
        """
        base = (metrics_confidence * 0.6) + (knowledge_relevance * 0.4)
        boost = min(pattern_count * 0.03, 0.10)
        return round(min(base + boost, 0.99), 2)

    @staticmethod
    def generate_reasoning(
        decision_type: str,
        supporting_patterns: List[str],
        current_status: str
    ) -> str:
        """
        Genera una explicación en texto claro justificando la recomendación tomada.
        """
        patterns_str = ", ".join(supporting_patterns) if supporting_patterns else "ningún patrón crítico"

        if decision_type == "fallback":
            return f"Decisión [fallback]: Estado actual ({current_status}) indica inestabilidad severa coincidente con patrones históricos ({patterns_str}). Se recomienda activar plan de contingencia de respaldo."
        elif decision_type == "investigate":
            return f"Decisión [investigate]: Anomalías detectadas en métricas ({current_status}) respaldadas por patrones ({patterns_str}). Se requiere inspección previa a continuar."
        elif decision_type == "optimize":
            return f"Decisión [optimize]: Runtime en condiciones operativas estables ({current_status}). Conocimiento histórico sugiere oportunidades de optimización basada en ({patterns_str})."
        else:
            return f"Decisión [continue]: Métricas runtime dentro de parámetros esperados ({current_status}). El conocimiento histórico respalda ejecución fluida con patrones ({patterns_str})."

    @staticmethod
    def evaluate_with_context(
        current_metrics: Dict[str, Any],
        validation_reports: List[Dict[str, Any]],
        knowledge_context: Union[DecisionKnowledgeContext, Dict[str, Any]]
    ) -> KnowledgeAwareDecisionReport:
        """
        Pondera métricas actuales, informes de validación y contexto histórico para generar un KnowledgeAwareDecisionReport.
        """
        error_rate = float(current_metrics.get("error_rate", 0.0))
        latency = float(current_metrics.get("avg_latency", 0.0))
        validations_passed = all(
            (v.get("success", False) if isinstance(v, dict) else getattr(v, "success", False))
            for v in validation_reports
        ) if validation_reports else True

        if isinstance(knowledge_context, dict):
            matched_str = knowledge_context.get("matched_patterns", "[]")
            relevance = float(knowledge_context.get("relevance_score", 0.5))
        else:
            matched_str = getattr(knowledge_context, "matched_patterns", "[]")
            relevance = float(getattr(knowledge_context, "relevance_score", 0.5))

        try:
            matched_patterns = json.loads(matched_str) if isinstance(matched_str, str) else matched_str
        except Exception:
            matched_patterns = []

        supporting_pattern_names = [p.get("pattern", "unknown") for p in matched_patterns if isinstance(p, dict)]
        source_knowledge_ids = [str(p.get("id")) for p in matched_patterns if isinstance(p, dict) and p.get("id")]
        source_ids_str = ",".join(source_knowledge_ids)

        has_failure_patterns = any(
            "failure" in str(p.get("knowledge_type", "")).lower() or "failure" in str(p.get("pattern", "")).lower()
            for p in matched_patterns if isinstance(p, dict)
        )

        # Determinación del tipo de decisión
        if not validations_passed or error_rate > 0.20:
            decision_type = "fallback"
            rec_action = "Activar procedimiento de degradación segura o fallback"
            metrics_conf = 0.90
        elif error_rate > 0.05 or has_failure_patterns or latency > 500:
            decision_type = "investigate"
            rec_action = "Inspecionar cuellos de botella y logs de observabilidad antes de continuar"
            metrics_conf = 0.80
        elif latency > 150 or any("optimization" in str(p.get("knowledge_type", "")).lower() for p in matched_patterns if isinstance(p, dict)):
            decision_type = "optimize"
            rec_action = "Aplicar optimizaciones de latencia y caché recomendadas"
            metrics_conf = 0.85
        else:
            decision_type = "continue"
            rec_action = "Continuar flujo de ejecución del runtime de forma normal"
            metrics_conf = 0.95

        final_conf = KnowledgeAwareReasoningEngine.calculate_decision_confidence(
            metrics_confidence=metrics_conf,
            knowledge_relevance=relevance,
            pattern_count=len(matched_patterns)
        )

        status_desc = f"error_rate={error_rate}, latency={latency}ms, valid={validations_passed}"
        reasoning_text = KnowledgeAwareReasoningEngine.generate_reasoning(
            decision_type=decision_type,
            supporting_patterns=supporting_pattern_names,
            current_status=status_desc
        )

        return KnowledgeAwareDecisionReport(
            source_knowledge_ids=source_ids_str,
            decision_type=decision_type,
            confidence=final_conf,
            supporting_patterns=", ".join(supporting_pattern_names),
            recommended_action=rec_action,
            reasoning=reasoning_text
        )
