import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.engine import OmniLocalEngine
from retrieval.models import RetrievalResult


def test_core_retrieval_integration():
    """
    Prueba unitaria para verificar la integración entre OmniLocalEngine y RetrievalEngine.
    """
    # 1. Prueba de Inicialización
    engine = OmniLocalEngine()
    assert engine.retrieval_engine is not None, "OmniLocalEngine debe inicializar retrieval_engine."
    assert engine.memory_manager is not None, "OmniLocalEngine debe inicializar memory_manager."
    assert engine.knowledge_manager is not None, "OmniLocalEngine debe inicializar knowledge_manager."

    # Crear memoria de prueba vía Core Engine
    mem_id = engine.save_memory(
        content="Estoy aprendiendo Python para OmniLocal Core",
        memory_type="learning",
        importance=0.9
    )
    assert mem_id > 0, "Debe retornar un ID de memoria válido."

    # Crear nodo de conocimiento de prueba vía KnowledgeManager expuesto
    node_id = engine.knowledge_manager.create_node(
        name="Python",
        node_type="technology",
        description="Lenguaje de programación principal"
    )
    assert node_id > 0, "Debe retornar un ID de nodo de conocimiento válido."

    # 2. Búsqueda de Memoria desde el Core Engine
    mem_results = engine.search_memory("Python")
    assert len(mem_results) >= 1, "search_memory en Core debe devolver al menos un resultado."
    assert any(r.source_type == "memory" and "Python" in r.content for r in mem_results)
    assert isinstance(mem_results[0], RetrievalResult)

    # 3. Búsqueda de Conocimiento desde el Core Engine
    know_results = engine.search_knowledge("Python")
    assert len(know_results) >= 1, "search_knowledge en Core debe devolver al menos un resultado."
    assert any(r.source_type == "knowledge_node" and "Python" in r.content for r in know_results)
    assert isinstance(know_results[0], RetrievalResult)

    # 4. Búsqueda Combinada desde el Core Engine
    combined_results = engine.search("Python")
    assert len(combined_results) >= 2, "search combinada en Core debe devolver memoria y conocimiento."

    has_memory = any(r.source_type == "memory" for r in combined_results)
    has_knowledge = any(r.source_type == "knowledge_node" for r in combined_results)
    assert has_memory and has_knowledge, "Búsqueda combinada del Core debe incluir ambos tipos de fuente."

    print("✅ test_core_retrieval.py: Integración de OmniLocalEngine con RetrievalEngine superada exitosamente.")


if __name__ == "__main__":
    test_core_retrieval_integration()
