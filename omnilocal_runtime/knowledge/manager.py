from typing import Optional, List, Dict, Any
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.learning.manager import RuntimeLearningManager
from omnilocal_runtime.observability.manager import RuntimeObservabilityManager
from omnilocal_runtime.knowledge.models import RuntimeKnowledgeEntry, RuntimeKnowledgeQuery
from omnilocal_runtime.knowledge.consolidation import RuntimeKnowledgeConsolidator
from omnilocal_runtime.knowledge.retrieval import RuntimeKnowledgeRetriever


class RuntimeKnowledgeManager:
    """
    Gestor Principal de Consolidación de Conocimiento Runtime (Runtime Block 09).
    Consolida aprendizajes históricos en un repositorio de conocimientos reutilizables
    y permite su consulta sin alterar workflows, ejecuciones o decisiones previas.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        learning_manager: Optional[RuntimeLearningManager] = None,
        obs_manager: Optional[RuntimeObservabilityManager] = None
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.learning_manager = learning_manager or RuntimeLearningManager(db_manager=self.db_manager)
        self.obs_manager = obs_manager or RuntimeObservabilityManager(db_manager=self.db_manager)

    def create_knowledge(
        self,
        knowledge_type: str,
        pattern: str,
        source_learning_id: int = 0,
        description: str = "",
        confidence: float = 0.0,
        usage_count: int = 1
    ) -> RuntimeKnowledgeEntry:
        """
        Crea y persiste un objeto RuntimeKnowledgeEntry en SQLite.
        """
        entry_id = self.db_manager.insert_knowledge_entry(
            knowledge_type=knowledge_type,
            pattern=pattern,
            source_learning_id=source_learning_id,
            description=description,
            confidence=confidence,
            usage_count=usage_count
        )

        return RuntimeKnowledgeEntry(
            id=entry_id,
            knowledge_type=knowledge_type,
            source_learning_id=source_learning_id,
            pattern=pattern,
            description=description,
            confidence=confidence,
            usage_count=usage_count
        )

    def consolidate_knowledge(self) -> Dict[str, Any]:
        """
        Lee los registros de aprendizaje de RuntimeLearningManager, los consolida
        e inserta las entradas de conocimiento correspondiente en SQLite.
        """
        learnings = self.learning_manager.get_learning_records()

        if not learnings:
            # Si no hay aprendizajes previos, ejecutamos el análisis de aprendizaje primero
            self.learning_manager.analyze_execution_history()
            learnings = self.learning_manager.get_learning_records()

        raw_entries = [RuntimeKnowledgeConsolidator.consolidate_learning(rec) for rec in learnings]
        merged_entries = RuntimeKnowledgeConsolidator.merge_similar_patterns(raw_entries)

        persisted_entries: List[RuntimeKnowledgeEntry] = []
        for entry in merged_entries:
            saved = self.create_knowledge(
                knowledge_type=entry.knowledge_type,
                pattern=entry.pattern,
                source_learning_id=entry.source_learning_id,
                description=entry.description,
                confidence=entry.confidence,
                usage_count=entry.usage_count
            )
            persisted_entries.append(saved)

        avg_confidence = RuntimeKnowledgeConsolidator.calculate_knowledge_confidence(persisted_entries)
        summary = RuntimeKnowledgeConsolidator.generate_knowledge_summary([e.to_dict() for e in persisted_entries])

        return {
            "source_learnings_processed": len(learnings),
            "consolidated_entries_created": len(persisted_entries),
            "average_confidence": avg_confidence,
            "summary": summary,
            "entries": [e.to_dict() for e in persisted_entries]
        }

    def query_knowledge(self, query_type: str, query_value: str) -> Dict[str, Any]:
        """
        Realiza una consulta sobre la base de conocimiento y registra la búsqueda.
        """
        # Registrar la consulta en SQLite
        self.db_manager.insert_knowledge_query(query_type=query_type, query_value=query_value)

        entries = self.get_knowledge_entries()

        if query_type == "high_confidence":
            min_conf = float(query_value) if query_value and query_value.replace('.', '', 1).isdigit() else 0.8
            matched = RuntimeKnowledgeRetriever.get_high_confidence_patterns(entries, min_confidence=min_conf)
        elif query_type == "related":
            matched = RuntimeKnowledgeRetriever.find_related_patterns(entries, pattern_name=query_value)
        else:
            matched = RuntimeKnowledgeRetriever.search_knowledge(entries, query_type=query_type, query_value=query_value)

        return {
            "query_type": query_type,
            "query_value": query_value,
            "results_count": len(matched),
            "results": matched
        }

    def get_knowledge_entries(self) -> List[Dict[str, Any]]:
        """Obtiene todas las entradas de conocimiento desde SQLite."""
        return self.db_manager.get_knowledge_entries()

    def get_knowledge_queries(self) -> List[Dict[str, Any]]:
        """Obtiene el historial de consultas registradas en SQLite."""
        return self.db_manager.get_knowledge_queries()
