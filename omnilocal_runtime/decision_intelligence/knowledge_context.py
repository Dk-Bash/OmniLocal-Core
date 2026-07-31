from typing import List, Dict, Any, Union
import json
from omnilocal_runtime.decision_intelligence.models import DecisionKnowledgeContext


class RuntimeKnowledgeContextBuilder:
    """
    Capa de Construcción de Contexto de Conocimiento para Decisiones (Runtime Block 10).
    Evalúa entradas de RuntimeKnowledgeEntry y genera contexto explicativo relevante.
    """

    @staticmethod
    def _extract_field(item: Union[Dict[str, Any], Any], field_name: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(field_name, default)
        return getattr(item, field_name, default)

    @staticmethod
    def calculate_relevance(entry: Any, current_state: Dict[str, Any]) -> float:
        """
        Calcula la puntuación de relevancia (0.0 - 1.0) de una entrada de conocimiento
        en función del estado actual del runtime (métricas, latencia, errores, etc.).
        """
        confidence = float(RuntimeKnowledgeContextBuilder._extract_field(entry, "confidence", 0.5))
        k_type = str(RuntimeKnowledgeContextBuilder._extract_field(entry, "knowledge_type", "")).lower()
        pattern = str(RuntimeKnowledgeContextBuilder._extract_field(entry, "pattern", "")).lower()

        relevance = confidence

        error_rate = float(current_state.get("error_rate", 0.0))
        latency = float(current_state.get("avg_latency", 0.0))
        cpu_usage = float(current_state.get("cpu_usage", 0.0))

        if "failure" in k_type or "failure" in pattern:
            if error_rate > 0.05 or current_state.get("has_errors"):
                relevance = min(relevance * 1.25, 0.99)
        elif "performance" in k_type or "latency" in pattern:
            if latency > 200 or cpu_usage > 70:
                relevance = min(relevance * 1.20, 0.99)
        elif "optimization" in k_type or "recovery" in k_type:
            relevance = min(relevance * 1.10, 0.95)

        return round(relevance, 2)

    @staticmethod
    def find_relevant_knowledge(
        knowledge_entries: List[Any],
        query_or_metrics: Dict[str, Any],
        min_relevance: float = 0.50
    ) -> List[Any]:
        """
        Filtra y devuelve las entradas de conocimiento cuyo puntaje de relevancia
        sea mayor o igual a min_relevance.
        """
        relevant = []
        for entry in knowledge_entries:
            score = RuntimeKnowledgeContextBuilder.calculate_relevance(entry, query_or_metrics)
            if score >= min_relevance:
                relevant.append({
                    "entry": entry,
                    "relevance_score": score
                })

        relevant.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant

    @staticmethod
    def build_context(
        knowledge_entries: List[Any],
        current_metrics: Dict[str, Any]
    ) -> DecisionKnowledgeContext:
        """
        Toma entradas de RuntimeKnowledgeEntry y genera un DecisionKnowledgeContext consolidado.
        """
        relevant_items = RuntimeKnowledgeContextBuilder.find_relevant_knowledge(knowledge_entries, current_metrics)

        matched_patterns = []
        total_score = 0.0

        for item in relevant_items:
            entry = item["entry"]
            score = item["relevance_score"]
            pattern = RuntimeKnowledgeContextBuilder._extract_field(entry, "pattern", "unknown")
            k_type = RuntimeKnowledgeContextBuilder._extract_field(entry, "knowledge_type", "unknown")
            desc = RuntimeKnowledgeContextBuilder._extract_field(entry, "description", "")
            entry_id = RuntimeKnowledgeContextBuilder._extract_field(entry, "id", 0)

            matched_patterns.append({
                "id": entry_id,
                "knowledge_type": k_type,
                "pattern": pattern,
                "description": desc,
                "relevance_score": score
            })
            total_score += score

        avg_relevance = round(total_score / len(relevant_items), 2) if relevant_items else 0.0
        query_summary = f"Evaluación de métricas runtime: error_rate={current_metrics.get('error_rate', 0)}, latency={current_metrics.get('avg_latency', 0)}ms"

        return DecisionKnowledgeContext(
            query=query_summary,
            matched_patterns=json.dumps(matched_patterns),
            relevance_score=avg_relevance
        )
