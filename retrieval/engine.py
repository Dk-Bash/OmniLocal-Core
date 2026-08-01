from collections import defaultdict
from typing import Dict, List, Optional

from memory.manager import MemoryManager
from knowledge.manager import KnowledgeManager
from retrieval.models import RetrievalResult
from retrieval.textutils import extract_keywords


class RetrievalEngine:
    """
    Motor de recuperación de información para OmniLocal-Core.
    Proporciona capacidades de búsqueda interna sobre memorias y nodos de conocimiento
    utilizando consultas de coincidencia SQL LIKE, sin requerir modelos de IA externos.

    La búsqueda es por palabras clave (no por la frase completa literal): se
    extraen los términos significativos de la consulta y se buscan por
    separado, puntuando cada resultado según cuántas palabras clave distintas
    contiene. Esto permite encontrar "mi nombre es Marcelo" al preguntar
    "¿cómo me llamo?", donde ninguna de las dos frases aparece completa
    dentro de la otra.
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
        Busca recuerdos por superposición de palabras clave con la consulta.
        Devuelve una lista de RetrievalResult con source_type="memory",
        ordenada de mayor a menor cantidad de palabras clave coincidentes.
        """
        keywords = extract_keywords(query)
        if not keywords:
            # Consulta demasiado corta/genérica (ej. "hola"): buscar tal cual.
            memories = self.memory_manager.search_memories(query)
            return [RetrievalResult(id=m.id, source_type="memory", content=m.content, score=1.0) for m in memories]

        matches: Dict[int, dict] = {}
        hit_count: Dict[int, int] = defaultdict(int)
        for kw in keywords:
            for mem in self.memory_manager.search_memories(kw):
                matches[mem.id] = mem
                hit_count[mem.id] += 1

        results = [
            RetrievalResult(id=mem.id, source_type="memory", content=mem.content, score=hit_count[mem.id] / len(keywords))
            for mem_id, mem in matches.items()
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def search_knowledge(self, query: str) -> List[RetrievalResult]:
        """
        Busca nodos de conocimiento por superposición de palabras clave.
        Devuelve una lista de RetrievalResult con source_type="knowledge_node",
        con el contenido = nombre + descripción del nodo (para no perder el
        cuerpo real de un documento ingerido), ordenada por relevancia.
        """
        keywords = extract_keywords(query)

        def node_content(node) -> str:
            if node.description and node.description.strip():
                return f"{node.name}: {node.description.strip()}"
            return node.name

        if not keywords:
            nodes = self.knowledge_manager.search_nodes(query)
            return [RetrievalResult(id=n.id, source_type="knowledge_node", content=node_content(n), score=1.0) for n in nodes]

        matches: Dict[int, object] = {}
        hit_count: Dict[int, int] = defaultdict(int)
        for kw in keywords:
            for node in self.knowledge_manager.search_nodes(kw):
                matches[node.id] = node
                hit_count[node.id] += 1

        results = [
            RetrievalResult(
                id=node.id,
                source_type="knowledge_node",
                content=node_content(node),
                score=hit_count[node.id] / len(keywords),
            )
            for node_id, node in matches.items()
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def search(self, query: str) -> List[RetrievalResult]:
        """
        Método principal de búsqueda que combina resultados de memoria y conocimiento,
        ordenados por relevancia (mayor superposición de palabras clave primero).
        """
        memory_results = self.search_memory(query)
        knowledge_results = self.search_knowledge(query)
        combined = memory_results + knowledge_results
        combined.sort(key=lambda r: r.score, reverse=True)
        return combined
