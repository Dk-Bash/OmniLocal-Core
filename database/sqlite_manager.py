import os
import sqlite3
import json
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

        # 15. Tabla maintenance_decisions (Módulo 30)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_type TEXT NOT NULL,
                selected_strategy TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT NOT NULL,
                supporting_factors TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 16. Tabla maintenance_execution_plans (Módulo 31)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_execution_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_type TEXT NOT NULL,
                strategy_type TEXT NOT NULL,
                execution_steps TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                estimated_duration TEXT NOT NULL,
                requires_approval INTEGER NOT NULL DEFAULT 0,
                reasoning TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 17. Tabla execution_validation_reports (Módulo 32)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_validation_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                valid INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                issues TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 18. Tabla execution_approvals (Módulo 33)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                validation_id INTEGER NOT NULL,
                approval_status TEXT NOT NULL,
                approved INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 19. Tabla execution_tracking (Módulo 34)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                approval_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                progress REAL NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 20. Tabla execution_results (Módulo 35)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id INTEGER NOT NULL,
                result_status TEXT NOT NULL,
                impact TEXT NOT NULL,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 21. Tabla execution_feedback (Módulo 36)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                feedback_type TEXT NOT NULL,
                quality_score REAL NOT NULL,
                learning_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 22. Tabla maintenance_knowledge (Módulo 37)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_feedback_id INTEGER NOT NULL,
                knowledge_type TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 23. Tabla maintenance_patterns (Módulo 38)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                occurrences INTEGER NOT NULL,
                confidence REAL NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 24. Tabla maintenance_improvements (Módulo 39)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER NOT NULL,
                recommendation_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        self.conn.commit()
