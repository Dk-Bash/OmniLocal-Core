from typing import List, Optional
from app.logger import get_logger
from database.sqlite_manager import SQLiteManager
from knowledge.models import KnowledgeNode, KnowledgeRelation

logger = get_logger(__name__)


class KnowledgeManager:
    """
    Gestor de la capa de conocimiento (Knowledge Layer) para OmniLocal-Core.
    Administra entidades (nodos) y sus relaciones delegando las operaciones SQL
    directamente en SQLiteManager y validando con los modelos Pydantic.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        if db_manager is None:
            self.db_manager = SQLiteManager()
            self.db_manager.connect()
            self.db_manager.create_tables()
        else:
            self.db_manager = db_manager

    def create_node(self, name: str, node_type: str, description: str = "") -> int:
        """
        Crea y valida un nuevo nodo de conocimiento.
        Delegando la inserción SQL a SQLiteManager.
        Devuelve el ID generado para el nodo.
        """
        node_obj = KnowledgeNode(
            name=name,
            node_type=node_type,
            description=description
        )

        created_id = self.db_manager.insert_knowledge_node(
            name=node_obj.name,
            node_type=node_obj.node_type,
            description=node_obj.description,
            created_at=node_obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        logger.info(f"Nodo de conocimiento '{name}' ({node_type}) creado con ID {created_id}.")
        return created_id

    def get_node(self, node_id: int) -> Optional[KnowledgeNode]:
        """
        Busca y recupera un nodo de conocimiento por su ID.
        Devuelve una instancia de KnowledgeNode o None si no existe.
        """
        row_dict = self.db_manager.get_knowledge_node(node_id)
        if row_dict is None:
            logger.info(f"Nodo con ID {node_id} no fue encontrado.")
            return None

        return KnowledgeNode(**row_dict)

    def create_relation(self, source_id: int, target_id: int, relation_type: str) -> int:
        """
        Crea una relación entre un nodo origen (source_id) y un nodo destino (target_id).
        Delegando la inserción SQL a SQLiteManager.
        Devuelve el ID generado para la relación.
        """
        relation_obj = KnowledgeRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type
        )

        created_id = self.db_manager.insert_knowledge_relation(
            source_id=relation_obj.source_id,
            target_id=relation_obj.target_id,
            relation_type=relation_obj.relation_type,
            created_at=relation_obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        logger.info(
            f"Relación '{relation_type}' creada entre nodo {source_id} y nodo {target_id} (ID {created_id})."
        )
        return created_id

    def get_relations(self, node_id: int) -> List[KnowledgeRelation]:
        """
        Obtiene todas las relaciones asociadas a un nodo (sea como nodo origen o destino).
        Devuelve una lista de instancias de KnowledgeRelation.
        """
        rows = self.db_manager.get_knowledge_relations(node_id)
        return [KnowledgeRelation(**row_dict) for row_dict in rows]

    def search_nodes(self, query: str) -> List[KnowledgeNode]:
        """
        Busca nodos de conocimiento por nombre, tipo o descripción (LIKE).
        Delegando la consulta SQL a SQLiteManager.
        """
        rows = self.db_manager.search_knowledge_nodes(query)
        return [KnowledgeNode(**row_dict) for row_dict in rows]
