import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retrieval.engine import RetrievalEngine
from retrieval.models import RetrievalResult


def test_retrieval_engine_operations():
    """
    Prueba unitaria para verificar las capacidades de búsqueda de RetrievalEngine.
    """
    engine = RetrievalEngine()

    # 1. Prueba de búsqueda en Memoria
    mem_id = engine.memory_manager.save_memory(
        content="Estoy aprendiendo Python para OmniLocal",
        memory_type="learning",
        importance=0.8
    )
    assert mem_id > 0

    mem_results = engine.search_memory("Python")
    assert len(mem_results) >= 1, "Debe encontrar al menos un recuerdo con 'Python'."
    assert any(r.source_type == "memory" and "Python" in r.content for r in mem_results)
    assert isinstance(mem_results[0], RetrievalResult)

    # 2. Prueba de búsqueda en Conocimiento
    node_id = engine.knowledge_manager.create_node(
        name="Python",
        node_type="technology",
        description="Lenguaje de programación de alto nivel"
    )
    assert node_id > 0

    know_results = engine.search_knowledge("Python")
    assert len(know_results) >= 1, "Debe encontrar al menos un nodo de conocimiento con 'Python'."
    assert any(r.source_type == "knowledge_node" and "Python" in r.content for r in know_results)
    assert isinstance(know_results[0], RetrievalResult)

    # 3. Prueba de búsqueda combinada (search)
    combined_results = engine.search("Python")
    assert len(combined_results) >= 2, "La búsqueda combinada debe devolver tanto memoria como conocimiento."

    has_memory = any(r.source_type == "memory" for r in combined_results)
    has_knowledge = any(r.source_type == "knowledge_node" for r in combined_results)
    assert has_memory and has_knowledge, "Debe contener tanto resultados de memoria como de conocimiento."

    print("✅ test_retrieval.py: Todas las operaciones de RetrievalEngine pasaron exitosamente.")


if __name__ == "__main__":
    test_retrieval_engine_operations()
