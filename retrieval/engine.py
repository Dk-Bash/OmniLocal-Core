from typing import List, Optional
from memory.manager import MemoryManager
from knowledge.manager import KnowledgeManager
from retrieval.models import RetrievalResult


class RetrievalEngine:
    """
    Motor de recuperación de información para OmniLocal-Core.
    Proporciona capacidades de búsqueda interna sobre memorias y nodos de conocimiento
    utilizando consultas de coincidencia SQL LIKE sin requerir modelos de IA externos.
    """

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        knowledge_manager: Optional[KnowledgeManager] = None
    ):
        if memory_manager is None:
            self.memory_manager = MemoryManager()
        else:
            self.memory_manager = memory_manager

        if knowledge_manager is None:
            self.knowledge_manager = KnowledgeManager(db_manager=self.memory_manager.db_manager)
        else:
            self.knowledge_manager = knowledge_manager

    def search_memory(self, query: str) -> List[RetrievalResult]:
        """
        Busca recuerdos por coincidencia de texto en la tabla memories.
        Devuelve una lista de instancias de RetrievalResult con source_type="memory".
        """
        memories = self.memory_manager.search_memories(query)
        results = []
        for mem in memories:
            results.append(
                RetrievalResult(
                    id=mem.id,
                    source_type="memory",
                    content=mem.content,
                    score=1.0
                )
            )
        return results

    def search_knowledge(self, query: str) -> List[RetrievalResult]:
        """
        Busca nodos de conocimiento por coincidencia de texto en la tabla knowledge_nodes.
        Devuelve una lista de instancias de RetrievalResult con source_type="knowledge_node".
        """
        nodes = self.knowledge_manager.search_nodes(query)
        results = []
        for node in nodes:
            results.append(
                RetrievalResult(
                    id=node.id,
                    source_type="knowledge_node",
                    content=node.name,
                    score=1.0
                )
            )
        return results

    def search(self, query: str) -> List[RetrievalResult]:
        """
        Método principal de búsqueda que combina resultados de memoria y conocimiento.
        """
        memory_results = self.search_memory(query)
        knowledge_results = self.search_knowledge(query)
        return memory_results + knowledge_results
