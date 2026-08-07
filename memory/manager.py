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

    def update_memory(
        self,
        memory_id: int,
        content: str,
        importance: Optional[float] = None,
        confidence: Optional[float] = None,
    ) -> bool:
        """
        Actualiza el contenido de una memoria existente (Bloque 6 -- Adaptive
        Memory Consolidation). Valida con Pydantic antes de escribir, mismo
        criterio que save_memory().
        """
        if importance is not None or confidence is not None:
            current = self.get_memory(memory_id)
            check_importance = importance if importance is not None else (current.importance if current else 0.5)
            check_confidence = confidence if confidence is not None else (current.confidence if current else 1.0)
            Memory(content=content, importance=check_importance, confidence=check_confidence)
        return self.db_manager.update_memory(memory_id, content, importance=importance, confidence=confidence)

    def mark_reviewed(self, memory_id: int, review_status: str) -> bool:
        """review_status: 'confirmado' | 'corregido' | 'ignorado' (Bloque 13)."""
        return self.db_manager.mark_memory_reviewed(memory_id, review_status)

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

    def search_memories(self, query: str) -> List[Memory]:
        """
        Busca recuerdos que contengan el texto de la consulta (LIKE).
        Delegando la consulta SQL a SQLiteManager.
        """
        rows = self.db_manager.search_memories(query)
        return [Memory(**row_dict) for row_dict in rows]
