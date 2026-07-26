from typing import List, Optional
import sqlite3
from memory.models import Memory
from database.sqlite_manager import SQLiteManager


class MemoryManager:
    """
    Gestor del motor de memoria para OmniLocal-Core.
    Interactúa con la base de datos SQLite para persistir y recuperar recuerdos
    utilizando los modelos Pydantic definidos en memory/models.py.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        if db_manager is None:
            self.db_manager = SQLiteManager()
            self.db_manager.connect()
            self.db_manager.create_tables()
        else:
            self.db_manager = db_manager

    def save_memory(self, content: str, memory_type: str = "episodic", importance: float = 0.5) -> int:
        """
        Crea y valida un recuerdo usando Pydantic, e inserta el registro en la tabla memories.
        Devuelve el ID generado por SQLite.
        """
        # Validar datos antes de insertar usando el modelo Memory
        memory_obj = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance
        )

        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO memories (content, memory_type, importance, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (
                memory_obj.content,
                memory_obj.memory_type,
                memory_obj.importance,
                memory_obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        conn.commit()
        created_id = cursor.lastrowid
        return created_id

    def get_memory(self, memory_id: int) -> Optional[Memory]:
        """
        Recupera un recuerdo por su ID y devuelve una instancia del modelo Memory o None si no existe.
        """
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?;", (memory_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        row_dict = dict(row)
        return Memory(**row_dict)

    def get_all_memories(self) -> List[Memory]:
        """
        Devuelve una lista con todos los recuerdos almacenados como instancias de Memory.
        """
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories ORDER BY id ASC;")
        rows = cursor.fetchall()

        memories = []
        for row in rows:
            row_dict = dict(row)
            memories.append(Memory(**row_dict))

        return memories

    def delete_memory(self, memory_id: int) -> bool:
        """
        Elimina un recuerdo de la base de datos por su ID.
        Devuelve True si el registro fue eliminado, o False si no existía.
        """
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?;", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0
