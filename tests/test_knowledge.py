import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from knowledge.manager import KnowledgeManager
from knowledge.models import KnowledgeNode, KnowledgeRelation


def test_knowledge_node_and_relation_operations():
    """
    Prueba unitaria para verificar la creación y recuperación de nodos y relaciones de conocimiento.
    """
    manager = KnowledgeManager()

    # 1. Crear nodo 1 ("Python")
    node1_id = manager.create_node(
        name="Python",
        node_type="technology",
        description="Lenguaje de programación"
    )
    assert isinstance(node1_id, int) and node1_id > 0, "create_node debe devolver un ID válido."

    # 2. Recuperar nodo 1
    node1 = manager.get_node(node1_id)
    assert node1 is not None, "get_node debe devolver el nodo creado."
    assert isinstance(node1, KnowledgeNode), "El resultado debe ser una instancia de KnowledgeNode."
    assert node1.name == "Python"
    assert node1.node_type == "technology"
    assert node1.description == "Lenguaje de programación"

    # 3. Crear nodo 2 ("Programación")
    node2_id = manager.create_node(
        name="Programación",
        node_type="concept",
        description="Disciplina de desarrollo de software"
    )
    assert isinstance(node2_id, int) and node2_id > 0

    # 4. Crear relación (Python -> pertenece_a -> Programación)
    relation_id = manager.create_relation(
        source_id=node1_id,
        target_id=node2_id,
        relation_type="pertenece_a"
    )
    assert isinstance(relation_id, int) and relation_id > 0, "create_relation debe devolver un ID válido."

    # 5. Obtener relaciones del nodo 1
    relations = manager.get_relations(node1_id)
    assert len(relations) >= 1, "Debe haber al menos 1 relación asociada al nodo 1."

    matched_rel = next((r for r in relations if r.id == relation_id), None)
    assert matched_rel is not None, "La relación creada debe ser devuelta por get_relations."
    assert isinstance(matched_rel, KnowledgeRelation)
    assert matched_rel.source_id == node1_id
    assert matched_rel.target_id == node2_id
    assert matched_rel.relation_type == "pertenece_a"

    print("✅ test_knowledge.py: Todas las operaciones de KnowledgeManager pasaron exitosamente.")


if __name__ == "__main__":
    test_knowledge_node_and_relation_operations()
