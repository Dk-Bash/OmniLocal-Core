import os
import sqlite3
from typing import Optional, Any
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
        """Crea las tres tablas iniciales obligatorias para el Módulo 2."""
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

        # 6. Tabla context_sessions (Módulo 10)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 7. Tabla context_messages (Módulo 10)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES context_sessions (id) ON DELETE CASCADE
            );
        """)

        # 8. Tabla user_profiles (Módulo 11)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                display_name TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'es',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 9. Tabla user_preferences (Módulo 11)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles (id) ON DELETE CASCADE
            );
        """)

        # 10. Tabla interaction_feedback (Módulo 14)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interaction_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                confidence REAL NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 11. Tabla maintenance_audit_events (Módulo 23)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                source_layer TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 12. Tabla maintenance_outcome_evaluations (Módulo 24)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_outcome_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                result_type TEXT NOT NULL,
                score REAL NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES maintenance_audit_events(id) ON DELETE CASCADE
            );
        """)

        # 13. Tabla strategy_evaluations (Módulo 27)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT NOT NULL,
                quality_score REAL NOT NULL,
                impact_score REAL NOT NULL,
                confidence_score REAL NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 14. Tabla adaptive_recommendations (Módulo 29)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptive_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_type TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                confidence REAL NOT NULL,
                reason TEXT NOT NULL,
                based_on_history INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    # ----------------------------------------------------
    # Operaciones CRUD para Context Engine (Módulo 10)
    # ----------------------------------------------------
    def insert_context_session(self, session_name: str, active: bool = True, created_at: Optional[str] = None) -> int:
        """Inserta una sesión de contexto en context_sessions y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        active_int = 1 if active else 0
        if created_at is None:
            cursor.execute(
                """
                INSERT INTO context_sessions (session_name, active)
                VALUES (?, ?);
                """,
                (session_name, active_int)
            )
        else:
            cursor.execute(
                """
                INSERT INTO context_sessions (session_name, active, created_at)
                VALUES (?, ?, ?);
                """,
                (session_name, active_int, created_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_context_session(self, session_id: int) -> Optional[dict]:
        """Recupera una sesión de contexto por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM context_sessions WHERE id = ?;", (session_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        d = dict(row)
        d['active'] = bool(d['active'])
        return d

    def update_context_session_active(self, session_id: int, active: bool) -> bool:
        """Actualiza el estado 'active' de una sesión de contexto."""
        conn = self.connect()
        cursor = conn.cursor()
        active_int = 1 if active else 0
        cursor.execute(
            "UPDATE context_sessions SET active = ? WHERE id = ?;",
            (active_int, session_id)
        )
        conn.commit()
        return cursor.rowcount > 0

    def insert_context_message(self, session_id: int, role: str, content: str, created_at: Optional[str] = None) -> int:
        """Inserta un mensaje de contexto en context_messages y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            cursor.execute(
                """
                INSERT INTO context_messages (session_id, role, content)
                VALUES (?, ?, ?);
                """,
                (session_id, role, content)
            )
        else:
            cursor.execute(
                """
                INSERT INTO context_messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (session_id, role, content, created_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_recent_context_messages(self, session_id: int, limit: int = 10) -> list:
        """Recupera los mensajes más recientes de una sesión en orden cronológico."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM (
                SELECT * FROM context_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC;
            """,
            (session_id, limit)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ----------------------------------------------------
    # Operaciones CRUD para User Profile & Preferences (Módulo 11)
    # ----------------------------------------------------
    def insert_user_profile(self, username: str, display_name: str, language: str = "es", created_at: Optional[str] = None) -> int:
        """Inserta un perfil de usuario en user_profiles y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            cursor.execute(
                """
                INSERT INTO user_profiles (username, display_name, language)
                VALUES (?, ?, ?);
                """,
                (username, display_name, language)
            )
        else:
            cursor.execute(
                """
                INSERT INTO user_profiles (username, display_name, language, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (username, display_name, language, created_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_user_profile(self, user_id: int) -> Optional[dict]:
        """Obtiene un perfil de usuario por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM user_profiles WHERE id = ?;",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_user_profile(self, user_id: int, display_name: Optional[str] = None, language: Optional[str] = None) -> bool:
        """Actualiza la información visible (nombre visible, idioma) de un usuario."""
        conn = self.connect()
        cursor = conn.cursor()
        updates = []
        params = []
        if display_name is not None:
            updates.append("display_name = ?")
            params.append(display_name)
        if language is not None:
            updates.append("language = ?")
            params.append(language)
        if not updates:
            return False
        params.append(user_id)
        query = f"UPDATE user_profiles SET {', '.join(updates)} WHERE id = ?;"
        cursor.execute(query, tuple(params))
        conn.commit()
        return cursor.rowcount > 0

    def set_user_preference(self, user_id: int, key: str, value: str, created_at: Optional[str] = None) -> int:
        """Guarda o actualiza una preferencia para un usuario."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM user_preferences WHERE user_id = ? AND key = ?;",
            (user_id, key)
        )
        existing = cursor.fetchone()
        if existing:
            pref_id = existing["id"]
            cursor.execute(
                "UPDATE user_preferences SET value = ? WHERE id = ?;",
                (value, pref_id)
            )
            conn.commit()
            return pref_id
        else:
            if created_at is None:
                cursor.execute(
                    """
                    INSERT INTO user_preferences (user_id, key, value)
                    VALUES (?, ?, ?);
                    """,
                    (user_id, key, value)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO user_preferences (user_id, key, value, created_at)
                    VALUES (?, ?, ?, ?);
                    """,
                    (user_id, key, value, created_at)
                )
            conn.commit()
            return cursor.lastrowid

    def get_user_preferences(self, user_id: int) -> list:
        """Obtiene todas las preferencias de un usuario."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM user_preferences WHERE user_id = ? ORDER BY id ASC;",
            (user_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ----------------------------------------------------
    # Operaciones CRUD para Self Evaluation & Feedback (Módulo 14)
    # ----------------------------------------------------
    def insert_interaction_feedback(
        self, interaction_id: int, rating: int, confidence: float, comment: str = "", created_at: Optional[str] = None
    ) -> int:
        """Inserta un registro de feedback de interacción en interaction_feedback y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            cursor.execute(
                """
                INSERT INTO interaction_feedback (interaction_id, rating, confidence, comment)
                VALUES (?, ?, ?, ?);
                """,
                (interaction_id, rating, confidence, comment)
            )
        else:
            cursor.execute(
                """
                INSERT INTO interaction_feedback (interaction_id, rating, confidence, comment, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (interaction_id, rating, confidence, comment, created_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_interaction_feedback_by_id(self, feedback_id: int) -> Optional[dict]:
        """Obtiene una evaluación/feedback por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM interaction_feedback WHERE id = ?;",
            (feedback_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_interaction_feedback_by_interaction(self, interaction_id: int) -> list:
        """Obtiene todas las evaluaciones asociadas a una interacción."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM interaction_feedback WHERE interaction_id = ? ORDER BY id ASC;",
            (interaction_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ----------------------------------------------------
    # Operaciones de Métricas y Analíticas (Módulo 15)
    # ----------------------------------------------------
    def count_memories(self) -> int:
        """Cuenta el total de registros en la tabla memories."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories;")
        row = cursor.fetchone()
        return row[0] if row else 0

    def count_sessions(self) -> int:
        """Cuenta el total de registros en la tabla context_sessions."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM context_sessions;")
        row = cursor.fetchone()
        return row[0] if row else 0

    def count_interactions(self) -> int:
        """Cuenta el total de interacciones (memorias episódicas)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories WHERE memory_type = 'episodic';")
        row = cursor.fetchone()
        return row[0] if row else 0

    def average_feedback_score(self) -> float:
        """Calcula el promedio de rating en interaction_feedback. Devuelve 0.0 si no existen registros."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(rating) FROM interaction_feedback;")
        row = cursor.fetchone()
        if row and row[0] is not None:
            return float(row[0])
        return 0.0

    # ----------------------------------------------------
    # Operaciones de Consolidación de Memoria (Módulo 16)
    # ----------------------------------------------------
    def count_memory_types(self) -> dict:
        """Devuelve un diccionario con la cantidad de memorias por tipo {memory_type: count}."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type;")
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows} if rows else {}

    def get_average_memory_importance(self) -> float:
        """Calcula el promedio del campo importance para todas las memorias. Devuelve 0.0 si no hay registros."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(importance) FROM memories;")
        row = cursor.fetchone()
        if row and row[0] is not None:
            return float(row[0])
        return 0.0

    # ----------------------------------------------------
    # Operaciones de Auditoría de Memoria (Módulo 17)
    # ----------------------------------------------------
    def get_all_memories_for_audit(self) -> list[dict]:
        """Recupera todas las memorias registradas para su auditoría de integridad."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ----------------------------------------------------
    # Operaciones de Auditoría de Mantenimiento (Módulo 23)
    # ----------------------------------------------------
    def insert_audit_event(
        self, event_type: str, source_layer: str, description: str, status: str, created_at: Optional[str] = None
    ) -> int:
        """Inserta un evento de auditoría de mantenimiento y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            cursor.execute(
                """
                INSERT INTO maintenance_audit_events (event_type, source_layer, description, status)
                VALUES (?, ?, ?, ?);
                """,
                (event_type, source_layer, description, status)
            )
        else:
            cursor.execute(
                """
                INSERT INTO maintenance_audit_events (event_type, source_layer, description, status, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (event_type, source_layer, description, status, created_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_audit_event(self, event_id: int) -> Optional[dict]:
        """Obtiene un evento de auditoría por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM maintenance_audit_events WHERE id = ?;",
            (event_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_audit_events(self) -> list[dict]:
        """Obtiene todos los eventos de auditoría ordenados cronológicamente (id ASC)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maintenance_audit_events ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ----------------------------------------------------
    # Operaciones CRUD para Maintenance Outcome Evaluation Layer (Módulo 24)
    # ----------------------------------------------------
    def insert_outcome_evaluation(
        self,
        event_id: int,
        result_type: str,
        score: float,
        summary: str,
        created_at: Optional[str] = None
    ) -> int:
        """Inserta una evaluación de resultado de mantenimiento y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            cursor.execute(
                """
                INSERT INTO maintenance_outcome_evaluations (event_id, result_type, score, summary)
                VALUES (?, ?, ?, ?);
                """,
                (event_id, result_type, score, summary)
            )
        else:
            cursor.execute(
                """
                INSERT INTO maintenance_outcome_evaluations (event_id, result_type, score, summary, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (event_id, result_type, score, summary, created_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_outcome_evaluation(self, evaluation_id: int) -> Optional[dict]:
        """Obtiene una evaluación de resultado por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM maintenance_outcome_evaluations WHERE id = ?;",
            (evaluation_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_outcomes_by_event(self, event_id: int) -> list[dict]:
        """Obtiene todas las evaluaciones asociadas a un evento de auditoría específico."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM maintenance_outcome_evaluations WHERE event_id = ? ORDER BY id ASC;",
            (event_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_all_outcome_evaluations(self) -> list[dict]:
        """Obtiene todas las evaluaciones de resultado ordenadas cronológicamente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maintenance_outcome_evaluations ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ----------------------------------------------------
    # Consultas analíticas para Maintenance Intelligence Layer (Módulo 25)
    # ----------------------------------------------------
    def count_outcome_events(self) -> int:
        """Cuenta el número total de evaluaciones de resultado registradas."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM maintenance_outcome_evaluations;")
        row = cursor.fetchone()
        return row[0] if row else 0

    def count_outcomes_by_type(self) -> dict:
        """Devuelve el conteo de evaluaciones agrupado por result_type."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT result_type, COUNT(*) FROM maintenance_outcome_evaluations GROUP BY result_type;"
        )
        rows = cursor.fetchall()
        result = {}
        for r_type, count in rows:
            if r_type:
                result[r_type] = count
        return result

    def average_outcome_score(self) -> float:
        """Calcula el promedio del score de las evaluaciones de resultado."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(score) FROM maintenance_outcome_evaluations;")
        row = cursor.fetchone()
        if row and row[0] is not None:
            return round(float(row[0]), 4)
        return 0.0

    def get_outcome_distribution(self) -> dict:
        """Obtiene la distribución general de los resultados de mantenimiento."""
        total = self.count_outcome_events()
        by_type = self.count_outcomes_by_type()
        avg_score = self.average_outcome_score()
        return {
            "total_events": total,
            "by_type": by_type,
            "average_score": avg_score,
        }

    # ----------------------------------------------------
    # Operaciones CRUD para Strategy Evaluation Layer (Módulo 27)
    # ----------------------------------------------------
    def insert_strategy_evaluation(
        self,
        strategy_id: Any,
        quality_score: float = 0.0,
        impact_score: float = 0.0,
        confidence_score: float = 0.0,
        summary: str = "",
        created_at: Optional[str] = None
    ) -> int:
        """Inserta una evaluación de estrategia en strategy_evaluations y devuelve el ID generado."""
        if isinstance(strategy_id, dict):
            data = strategy_id
            s_id = data.get("strategy_id", "strategy_001")
            q_score = data.get("quality_score", 0.0)
            i_score = data.get("impact_score", 0.0)
            c_score = data.get("confidence_score", 0.0)
            sum_text = data.get("summary", "")
            c_at = data.get("created_at")
        else:
            s_id = strategy_id
            q_score = quality_score
            i_score = impact_score
            c_score = confidence_score
            sum_text = summary
            c_at = created_at

        conn = self.connect()
        cursor = conn.cursor()
        if c_at:
            cursor.execute(
                """
                INSERT INTO strategy_evaluations (strategy_id, quality_score, impact_score, confidence_score, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (str(s_id), float(q_score), float(i_score), float(c_score), str(sum_text), str(c_at))
            )
        else:
            cursor.execute(
                """
                INSERT INTO strategy_evaluations (strategy_id, quality_score, impact_score, confidence_score, summary)
                VALUES (?, ?, ?, ?, ?);
                """,
                (str(s_id), float(q_score), float(i_score), float(c_score), str(sum_text))
            )
        conn.commit()
        return cursor.lastrowid

    def get_strategy_evaluation(self, eval_id: int) -> Optional[dict]:
        """Obtiene una evaluación de estrategia por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, strategy_id, quality_score, impact_score, confidence_score, summary, created_at FROM strategy_evaluations WHERE id = ?;",
            (eval_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "strategy_id": row["strategy_id"],
                "quality_score": row["quality_score"],
                "impact_score": row["impact_score"],
                "confidence_score": row["confidence_score"],
                "summary": row["summary"],
                "created_at": str(row["created_at"]),
            }
        return None

    def get_strategy_evaluations(self) -> list:
        """Obtiene todas las evaluaciones de estrategia ordenadas por id descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, strategy_id, quality_score, impact_score, confidence_score, summary, created_at FROM strategy_evaluations ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "strategy_id": row["strategy_id"],
                "quality_score": row["quality_score"],
                "impact_score": row["impact_score"],
                "confidence_score": row["confidence_score"],
                "summary": row["summary"],
                "created_at": str(row["created_at"]),
            })
        return result

    def count_strategy_evaluations(self) -> int:
        """Cuenta el total de evaluaciones registradas."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM strategy_evaluations;")
        row = cursor.fetchone()
        return row[0] if row else 0

    def average_strategy_quality(self) -> float:
        """Calcula el promedio de quality_score de las evaluaciones estratégicas."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(quality_score) FROM strategy_evaluations;")
        row = cursor.fetchone()
        return round(float(row[0]), 4) if (row and row[0] is not None) else 0.0

    def average_strategy_impact(self) -> float:
        """Calcula el promedio de impact_score de las evaluaciones estratégicas."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(impact_score) FROM strategy_evaluations;")
        row = cursor.fetchone()
        return round(float(row[0]), 4) if (row and row[0] is not None) else 0.0

    def average_strategy_confidence(self) -> float:
        """Calcula el promedio de confidence_score de las evaluaciones estratégicas."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(confidence_score) FROM strategy_evaluations;")
        row = cursor.fetchone()
        return round(float(row[0]), 4) if (row and row[0] is not None) else 0.0

    def get_best_strategy_type(self) -> Optional[str]:
        """Obtiene el tipo o identificador de estrategia con la mayor puntuación de calidad (quality_score)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT strategy_id FROM strategy_evaluations ORDER BY quality_score DESC, id DESC LIMIT 1;"
        )
        row = cursor.fetchone()
        if row and row["strategy_id"]:
            s_id = str(row["strategy_id"])
            s_lower = s_id.lower()
            if "immediate" in s_lower:
                return "immediate"
            elif "soon" in s_lower:
                return "soon"
            elif "planned" in s_lower:
                return "planned"
            elif "deferred" in s_lower:
                return "deferred"
            return s_id
        return None

    # ----------------------------------------------------
    # Operaciones CRUD para Adaptive Recommendation Layer (Módulo 29)
    # ----------------------------------------------------
    def insert_adaptive_recommendation(
        self,
        strategy_type: Any,
        recommended_action: Optional[str] = None,
        confidence: Optional[float] = None,
        reason: Optional[str] = None,
        based_on_history: Optional[bool] = None,
        created_at: Optional[Any] = None,
    ) -> int:
        """Inserta una recomendación adaptativa en la tabla adaptive_recommendations."""
        if hasattr(strategy_type, "strategy_type"):
            rec = strategy_type
            s_type = str(rec.strategy_type)
            r_act = str(rec.recommended_action)
            conf = float(rec.confidence)
            reas = str(rec.reason)
            b_hist = 1 if rec.based_on_history else 0
            c_at = rec.created_at.isoformat() if hasattr(rec.created_at, "isoformat") else str(rec.created_at)
        elif isinstance(strategy_type, dict):
            s_type = str(strategy_type.get("strategy_type", "unknown"))
            r_act = str(strategy_type.get("recommended_action", ""))
            conf = float(strategy_type.get("confidence", 0.0))
            reas = str(strategy_type.get("reason", ""))
            b_hist = 1 if strategy_type.get("based_on_history") else 0
            c_at = str(strategy_type.get("created_at")) if strategy_type.get("created_at") else None
        else:
            s_type = str(strategy_type)
            r_act = str(recommended_action or "")
            conf = float(confidence or 0.0)
            reas = str(reason or "")
            b_hist = 1 if based_on_history else 0
            c_at = str(created_at) if created_at else None

        conn = self.connect()
        cursor = conn.cursor()
        if c_at is None:
            cursor.execute(
                """
                INSERT INTO adaptive_recommendations (strategy_type, recommended_action, confidence, reason, based_on_history)
                VALUES (?, ?, ?, ?, ?);
                """,
                (s_type, r_act, conf, reas, b_hist)
            )
        else:
            cursor.execute(
                """
                INSERT INTO adaptive_recommendations (strategy_type, recommended_action, confidence, reason, based_on_history, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (s_type, r_act, conf, reas, b_hist, c_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_adaptive_recommendation(self, rec_id: int) -> Optional[dict]:
        """Obtiene una recomendación adaptativa por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, strategy_type, recommended_action, confidence, reason, based_on_history, created_at FROM adaptive_recommendations WHERE id = ?;",
            (rec_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "strategy_type": row["strategy_type"],
                "recommended_action": row["recommended_action"],
                "confidence": row["confidence"],
                "reason": row["reason"],
                "based_on_history": bool(row["based_on_history"]),
                "created_at": str(row["created_at"]),
            }
        return None

    def get_adaptive_recommendations(self) -> list:
        """Obtiene todas las recomendaciones adaptativas ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, strategy_type, recommended_action, confidence, reason, based_on_history, created_at FROM adaptive_recommendations ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "strategy_type": row["strategy_type"],
                "recommended_action": row["recommended_action"],
                "confidence": row["confidence"],
                "reason": row["reason"],
                "based_on_history": bool(row["based_on_history"]),
                "created_at": str(row["created_at"]),
            })
        return result

    def close(self) -> None:
        """Cierra la conexión activa con la base de datos."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
