import os
import sqlite3
from typing import Optional
from app.config import DATABASE_PATH


class SQLiteManager:
    """
    Gestor de base de datos SQLite para OmniLocal-Core.
    Maneja la conexión, creación de tablas e interacciones con data/omnilocal.db.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DATABASE_PATH
        self.conn: Optional[sqlite3.Connection] = None

        # Asegurar que el directorio de almacenamiento de la base de datos exista
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """Establece y devuelve una conexión a la base de datos SQLite."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            # Habilitar soporte para tipos de fecha y claves foráneas si fuera necesario
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def create_tables(self) -> None:
        """Crea las tablas obligatorias para OmniLocal-Core."""
        if self.conn is None:
            self.connect()

        cursor = self.conn.cursor()

        # 1. Tabla users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Tabla memories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                memory_type TEXT,
                importance REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Tabla conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Tabla knowledge_nodes (Módulo 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                node_type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. Tabla knowledge_relations (Módulo 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES knowledge_nodes (id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES knowledge_nodes (id) ON DELETE CASCADE
            );
        """)

        self.conn.commit()

    # ----------------------------------------------------
    # Operaciones CRUD para Knowledge Layer (Módulo 7)
    # ----------------------------------------------------
    def insert_knowledge_node(self, name: str, node_type: str, description: str = "", created_at: Optional[str] = None) -> int:
        """Inserta un nodo de conocimiento en la tabla knowledge_nodes y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            cursor.execute(
                """
                INSERT INTO knowledge_nodes (name, node_type, description)
                VALUES (?, ?, ?);
                """,
                (name, node_type, description)
            )
        else:
            cursor.execute(
                """
                INSERT INTO knowledge_nodes (name, node_type, description, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (name, node_type, description, created_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_knowledge_node(self, node_id: int) -> Optional[dict]:
        """Recupera un nodo de conocimiento por ID devolviendo un diccionario o None."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM knowledge_nodes WHERE id = ?;", (node_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def insert_knowledge_relation(self, source_id: int, target_id: int, relation_type: str, created_at: Optional[str] = None) -> int:
        """Inserta una relación de conocimiento en la tabla knowledge_relations y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            cursor.execute(
                """
                INSERT INTO knowledge_relations (source_id, target_id, relation_type)
                VALUES (?, ?, ?);
                """,
                (source_id, target_id, relation_type)
            )
        else:
            cursor.execute(
                """
                INSERT INTO knowledge_relations (source_id, target_id, relation_type, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (source_id, target_id, relation_type, created_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_knowledge_relations(self, node_id: int) -> list:
        """Recupera todas las relaciones asociadas a un nodo (source o target)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM knowledge_relations
            WHERE source_id = ? OR target_id = ?
            ORDER BY id ASC;
            """,
            (node_id, node_id)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search_memories(self, query: str) -> list:
        """Busca recuerdos cuyo contenido coincida con la consulta (LIKE)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM memories WHERE content LIKE ? ORDER BY id ASC;",
            (f"%{query}%",)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search_knowledge_nodes(self, query: str) -> list:
        """Busca nodos de conocimiento cuyo nombre, descripción o tipo coincidan con la consulta (LIKE)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_nodes WHERE name LIKE ? OR description LIKE ? OR node_type LIKE ? ORDER BY id ASC;",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        """Cierra la conexión activa con la base de datos."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
