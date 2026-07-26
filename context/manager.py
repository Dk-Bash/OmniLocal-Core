from typing import List, Optional
from app.logger import get_logger
from database.sqlite_manager import SQLiteManager
from context.models import ContextSession, ContextMessage

logger = get_logger(__name__)


class ContextManager:
    """
    Gestor de contexto conversacional para OmniLocal-Core.
    Administra sesiones de contexto y mensajes sin escribir SQL directo,
    delegando todas las interacciones de persistencia a SQLiteManager.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.db_manager = db_manager or SQLiteManager()
        self.db_manager.create_tables()
        logger.info("ContextManager inicializado correctamente.")

    def create_session(self, session_name: str) -> int:
        """
        Crea una nueva sesión de contexto conversacional.
        """
        session = ContextSession(session_name=session_name, active=True)
        session_id = self.db_manager.insert_context_session(
            session_name=session.session_name,
            active=session.active
        )
        logger.info(f"Sesión de contexto '{session_name}' creada con ID {session_id}.")
        return session_id

    def add_message(self, session_id: int, role: str, content: str) -> int:
        """
        Agrega un nuevo mensaje a una sesión de contexto existente.
        """
        message = ContextMessage(session_id=session_id, role=role, content=content)
        msg_id = self.db_manager.insert_context_message(
            session_id=message.session_id,
            role=message.role,
            content=message.content
        )
        logger.info(f"Mensaje rol '{role}' agregado a la sesión {session_id} con ID {msg_id}.")
        return msg_id

    def get_recent_messages(self, session_id: int, limit: int = 10) -> List[ContextMessage]:
        """
        Obtiene los últimos mensajes recientes de una sesión de contexto.
        """
        raw_msgs = self.db_manager.get_recent_context_messages(session_id=session_id, limit=limit)
        messages = []
        for msg_dict in raw_msgs:
            messages.append(ContextMessage(**msg_dict))
        return messages

    def close_session(self, session_id: int) -> bool:
        """
        Cierra una sesión de contexto cambiando active=True a active=False.
        """
        success = self.db_manager.update_context_session_active(session_id=session_id, active=False)
        if success:
            logger.info(f"Sesión de contexto {session_id} cerrada (active=False).")
        else:
            logger.warning(f"No se pudo cerrar la sesión de contexto {session_id}.")
        return success

    def get_session(self, session_id: int) -> Optional[ContextSession]:
        """
        Recupera una sesión de contexto por su ID.
        """
        s_dict = self.db_manager.get_context_session(session_id=session_id)
        if s_dict:
            return ContextSession(**s_dict)
        return None
