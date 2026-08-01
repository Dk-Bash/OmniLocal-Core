from collections import defaultdict
from typing import Dict, List, Optional

from memory.manager import MemoryManager
from knowledge.manager import KnowledgeManager
from retrieval.models import RetrievalResult
from retrieval.textutils import extract_keywords
from local_ai.embeddings import cosine_similarity
from local_ai.ollama_client import OllamaUnavailableError


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

    Bloque 3 (Memory Ranking Intelligence): el ranking de memorias además
    pondera por `importance`, no solo por coincidencia de palabras clave
    (ver docstring de search_memory). El conocimiento (search_knowledge)
    no se modificó: KnowledgeNode no tiene campo de importancia.
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
        ordenada de mayor a menor relevancia.

        Bloque 3 (Memory Ranking Intelligence): el score ya no depende solo
        de cuántas palabras clave coinciden -- también pesa la importancia
        de la memoria (`Memory.importance`, 0.0-1.0). Una memoria marcada
        como más importante (ej. un hecho guardado explícitamente) rankea
        por encima de una charla genérica vieja con la misma coincidencia
        de palabras. El multiplicador de importancia queda acotado a
        [0.5, 1.0] para que una coincidencia real de palabras clave nunca
        llegue a score 0 solo porque la importancia es baja.
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

        results = []
        for mem_id, mem in matches.items():
            keyword_score = hit_count[mem_id] / len(keywords)
            importance_multiplier = 0.5 + 0.5 * mem.importance
            results.append(
                RetrievalResult(id=mem.id, source_type="memory", content=mem.content, score=keyword_score * importance_multiplier)
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def search_memory_lexical(self, query: str) -> List[RetrievalResult]:
        """
        Igual que search_memory(), pero SIN el multiplicador de importancia
        del Bloque 3 -- devuelve el score léxico "puro" (superposición de
        palabras clave, 0.0-1.0). Existe para la capa híbrida (Bloque 5,
        ver retrieval/hybrid.py), que necesita keyword_score, semantic_score
        e importance como tres entradas independientes, sin contar la
        importancia dos veces. No modifica ni es usado por search_memory();
        es un método hermano, completamente aditivo.
        """
        keywords = extract_keywords(query)
        if not keywords:
            memories = self.memory_manager.search_memories(query)
            return [RetrievalResult(id=m.id, source_type="memory", content=m.content, score=1.0) for m in memories]

        matches: Dict[int, dict] = {}
        hit_count: Dict[int, int] = defaultdict(int)
        for kw in keywords:
            for mem in self.memory_manager.search_memories(kw):
                matches[mem.id] = mem
                hit_count[mem.id] += 1

        results = [
            RetrievalResult(id=mem.id, source_type="memory", content=mem.content, score=hit_count[mem_id] / len(keywords))
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

    def search_semantic(self, query: str, ollama, top_k: int = 5, min_similarity: float = 0.5) -> List[RetrievalResult]:
        """
        Bloque 4A: búsqueda por similitud de embeddings (comprensión
        semántica real, no por palabras clave). Completamente separada de
        `search()` -- todavía no se usa en el flujo de conversación (eso
        queda para el Bloque 4B). Existe para poder probarse y validarse
        de forma aislada, sin tocar el camino ya probado y en uso.

        Requiere que las memorias ya tengan un embedding guardado (ver
        local_ai/embeddings.py). Si Ollama o el modelo de embeddings no
        están disponibles, devuelve una lista vacía en vez de fallar.
        """
        if not ollama.has_embedding_model():
            return []
        try:
            query_vector = ollama.embed(query)
        except OllamaUnavailableError:
            return []
        if not query_vector:
            return []

        rows = self.memory_manager.db_manager.get_all_memory_embeddings()
        scored: List[RetrievalResult] = []
        for row in rows:
            similarity = cosine_similarity(query_vector, row["vector"])
            if similarity < min_similarity:
                continue
            memory = self.memory_manager.get_memory(row["memory_id"])
            if memory is None:
                continue
            scored.append(RetrievalResult(id=memory.id, source_type="memory_semantic", content=memory.content, score=similarity))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

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
