from typing import List, Dict, Any, Optional
from omnilocal_runtime.knowledge.models import RuntimeKnowledgeEntry


class RuntimeKnowledgeConsolidator:
    """
    Capa de Consolidador de Conocimiento del Runtime (Runtime Block 09).
    Transforma registros de aprendizaje en conocimiento reutilizable estructurado.
    """

    @staticmethod
    def map_learning_type_to_knowledge_type(learning_type: str) -> str:
        type_map = {
            "failure_pattern": "failure_pattern",
            "performance": "performance_pattern",
            "optimization": "optimization_pattern",
            "recovery": "recovery_pattern"
        }
        return type_map.get(learning_type.lower(), "performance_pattern")

    @staticmethod
    def consolidate_learning(learning_record: Any) -> RuntimeKnowledgeEntry:
        """
        Transforma un RuntimeLearningRecord (o dict equivalente) en un RuntimeKnowledgeEntry.
        """
        if isinstance(learning_record, dict):
            learning_id = learning_record.get("id", 0)
            l_type = learning_record.get("learning_type", "performance")
            pattern = learning_record.get("pattern_detected", "unknown_pattern")
            confidence = learning_record.get("confidence", 0.5)
            impact = learning_record.get("impact_prediction", "")
        else:
            learning_id = getattr(learning_record, "id", 0) or 0
            l_type = getattr(learning_record, "learning_type", "performance")
            pattern = getattr(learning_record, "pattern_detected", "unknown_pattern")
            confidence = getattr(learning_record, "confidence", 0.5)
            impact = getattr(learning_record, "impact_prediction", "")

        k_type = RuntimeKnowledgeConsolidator.map_learning_type_to_knowledge_type(l_type)
        description = f"Patrón de {k_type} consolidado ({pattern}). {impact}".strip()

        return RuntimeKnowledgeEntry(
            source_learning_id=learning_id,
            knowledge_type=k_type,
            pattern=pattern,
            description=description,
            confidence=confidence,
            usage_count=1
        )

    @staticmethod
    def merge_similar_patterns(entries: List[Any]) -> List[RuntimeKnowledgeEntry]:
        """
        Agrupa patrones idénticos o similares combinando sus apariciones e incrementando usage_count y confianza.
        """
        grouped: Dict[str, Dict[str, Any]] = {}

        for entry in entries:
            if isinstance(entry, dict):
                pattern = entry.get("pattern", "unknown")
                k_type = entry.get("knowledge_type", "performance_pattern")
                confidence = entry.get("confidence", 0.5)
                usage = entry.get("usage_count", 1)
                desc = entry.get("description", "")
                src_id = entry.get("source_learning_id", 0)
                entry_id = entry.get("id", None)
            else:
                pattern = getattr(entry, "pattern", "unknown")
                k_type = getattr(entry, "knowledge_type", "performance_pattern")
                confidence = getattr(entry, "confidence", 0.5)
                usage = getattr(entry, "usage_count", 1)
                desc = getattr(entry, "description", "")
                src_id = getattr(entry, "source_learning_id", 0)
                entry_id = getattr(entry, "id", None)

            key = f"{k_type}::{pattern}"

            if key not in grouped:
                grouped[key] = {
                    "id": entry_id,
                    "knowledge_type": k_type,
                    "source_learning_id": src_id,
                    "pattern": pattern,
                    "description": desc,
                    "confidence_sum": confidence,
                    "count": 1,
                    "total_usage": usage,
                }
            else:
                grouped[key]["confidence_sum"] += confidence
                grouped[key]["count"] += 1
                grouped[key]["total_usage"] += usage

        consolidated: List[RuntimeKnowledgeEntry] = []
        for key, item in grouped.items():
            avg_conf = item["confidence_sum"] / item["count"]
            boosted_conf = min(round(avg_conf + (item["count"] - 1) * 0.05, 2), 0.99)
            consolidated.append(
                RuntimeKnowledgeEntry(
                    id=item["id"],
                    knowledge_type=item["knowledge_type"],
                    source_learning_id=item["source_learning_id"],
                    pattern=item["pattern"],
                    description=item["description"],
                    confidence=boosted_conf,
                    usage_count=item["total_usage"]
                )
            )

        return consolidated

    @staticmethod
    def calculate_knowledge_confidence(learnings: List[Any]) -> float:
        """
        Calcula el nivel promedio de confiabilidad de un conjunto de conocimientos o aprendizajes.
        """
        if not learnings:
            return 0.50

        total_conf = 0.0
        for item in learnings:
            if isinstance(item, dict):
                total_conf += item.get("confidence", 0.5)
            else:
                total_conf += getattr(item, "confidence", 0.5)

        avg = total_conf / len(learnings)
        return round(avg, 2)

    @staticmethod
    def generate_knowledge_summary(entries: List[Any]) -> str:
        """
        Genera un resumen textual consolidado del base de conocimiento.
        """
        if not entries:
            return "Base de conocimiento runtime vacía."

        total = len(entries)
        high_conf = sum(1 for e in entries if (e.get("confidence", 0) if isinstance(e, dict) else getattr(e, "confidence", 0)) >= 0.8)

        return f"Consolidación completa: {total} entradas de conocimiento registradas ({high_conf} con alta confiabilidad >= 80%)."
