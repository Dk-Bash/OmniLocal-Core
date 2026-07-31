from typing import List, Dict, Any, Union


class RuntimeKnowledgeRetriever:
    """
    Capa de Recuperación y Búsqueda de Conocimiento Runtime (Runtime Block 09).
    Operaciones puramente de solo lectura sobre entradas de conocimiento consolidadas.
    """

    @staticmethod
    def _extract_field(item: Union[Dict[str, Any], Any], field_name: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(field_name, default)
        return getattr(item, field_name, default)

    @staticmethod
    def search_knowledge(
        entries: List[Any],
        query_type: str,
        query_value: str
    ) -> List[Any]:
        """
        Busca entradas de conocimiento según tipo de consulta ('knowledge_type', 'pattern', 'description' o 'all').
        """
        if not query_value:
            return entries

        q_val = query_value.lower()
        q_type = query_type.lower()
        results = []

        for item in entries:
            k_type = str(RuntimeKnowledgeRetriever._extract_field(item, "knowledge_type", "")).lower()
            pattern = str(RuntimeKnowledgeRetriever._extract_field(item, "pattern", "")).lower()
            desc = str(RuntimeKnowledgeRetriever._extract_field(item, "description", "")).lower()

            match = False
            if q_type == "knowledge_type" and q_val in k_type:
                match = True
            elif q_type == "pattern" and q_val in pattern:
                match = True
            elif q_type == "description" and q_val in desc:
                match = True
            elif q_type in ["all", "general", "search"]:
                if q_val in k_type or q_val in pattern or q_val in desc:
                    match = True

            if match:
                results.append(item)

        return results

    @staticmethod
    def find_related_patterns(
        entries: List[Any],
        pattern_name: str
    ) -> List[Any]:
        """
        Encuentra patrones relacionados por nombre parcial o tokens comunes.
        """
        if not pattern_name:
            return []

        tokens = [t.lower() for t in pattern_name.replace("_", " ").split() if len(t) > 2]
        results = []

        for item in entries:
            pattern = str(RuntimeKnowledgeRetriever._extract_field(item, "pattern", "")).lower()
            if any(token in pattern for token in tokens):
                results.append(item)

        return results

    @staticmethod
    def get_high_confidence_patterns(
        entries: List[Any],
        min_confidence: float = 0.8
    ) -> List[Any]:
        """
        Filtra y devuelve solo aquellos patrones con un nivel de confianza igual o superior a min_confidence.
        """
        results = []
        for item in entries:
            conf = float(RuntimeKnowledgeRetriever._extract_field(item, "confidence", 0.0))
            if conf >= min_confidence:
                results.append(item)

        return sorted(
            results,
            key=lambda x: float(RuntimeKnowledgeRetriever._extract_field(x, "confidence", 0.0)),
            reverse=True
        )
