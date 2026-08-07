from typing import List, Optional

from database.sqlite_manager import SQLiteManager
from goals.models import Goal


class GoalManager:
    """
    Gestor de objetivos/recordatorios para OmniLocal-Core (Bloque 9 --
    Goal & Reminder Foundation). Mismo patrón que MemoryManager: valida
    con Pydantic, delega el acceso a datos a SQLiteManager.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        if db_manager is None:
            self.db_manager = SQLiteManager()
            self.db_manager.connect()
            self.db_manager.create_tables()
        else:
            self.db_manager = db_manager

    def create_goal(
        self,
        content: str,
        due_at: Optional[str] = None,
        goal_type: str = "task",
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> int:
        """Crea un objetivo/recordatorio nuevo, en estado 'pendiente'."""
        goal_obj = Goal(content=content, goal_type=goal_type, category=category, description=description)  # valida antes de insertar
        return self.db_manager.insert_goal(
            goal_obj.content, due_at=due_at, goal_type=goal_obj.goal_type,
            category=goal_obj.category, description=goal_obj.description
        )

    def update_goal(self, goal_id: int, content: Optional[str] = None, due_at: Optional[str] = None) -> bool:
        """Actualiza contenido y/o fecha de un objetivo existente (Bloque 10)."""
        return self.db_manager.update_goal(goal_id, content=content, due_at=due_at)

    def cancel_goal(self, goal_id: int) -> bool:
        return self.db_manager.cancel_goal(goal_id)

    def get_goal(self, goal_id: int) -> Optional[Goal]:
        row = self.db_manager.get_goal(goal_id)
        return Goal(**row) if row else None

    def list_pending(self) -> List[Goal]:
        rows = self.db_manager.get_goals(status="pendiente")
        return [Goal(**row) for row in rows]

    def list_all(self) -> List[Goal]:
        rows = self.db_manager.get_goals()
        return [Goal(**row) for row in rows]

    def complete_goal(self, goal_id: int) -> bool:
        return self.db_manager.complete_goal(goal_id)

    def delete_goal(self, goal_id: int) -> bool:
        return self.db_manager.delete_goal(goal_id)
