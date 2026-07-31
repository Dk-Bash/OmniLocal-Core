import os
import sqlite3
import json
from datetime import datetime
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

        # 25. Tabla maintenance_correlations (Módulo 40)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_type TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                success_rate REAL NOT NULL,
                sample_size INTEGER NOT NULL,
                confidence REAL NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 26. Tabla adaptive_decisions (Módulo 41)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptive_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                correlation_id INTEGER NOT NULL,
                decision_type TEXT NOT NULL,
                recommended_strategy TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (correlation_id) REFERENCES maintenance_correlations(id) ON DELETE CASCADE
            );
        """)

        # 27. Tabla optimization_feedback (Módulo 42)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                previous_confidence REAL NOT NULL,
                new_confidence REAL NOT NULL,
                improvement_score REAL NOT NULL,
                optimization_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (decision_id) REFERENCES adaptive_decisions(id) ON DELETE CASCADE
            );
        """)

        # 28. Tabla maintenance_workflows (Módulo 43)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                workflow_type TEXT NOT NULL,
                steps TEXT NOT NULL,
                current_step INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 29. Tabla maintenance_policy_results (Módulo 44)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_policy_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER NOT NULL,
                allowed INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                violations TEXT,
                reasoning TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_id) REFERENCES maintenance_workflows(id) ON DELETE CASCADE
            );
        """)

        # 30. Tabla maintenance_coordination_results (Módulo 45)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_coordination_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER NOT NULL,
                policy_id INTEGER NOT NULL,
                coordination_status TEXT NOT NULL,
                next_action TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_id) REFERENCES maintenance_workflows(id) ON DELETE CASCADE,
                FOREIGN KEY (policy_id) REFERENCES maintenance_policy_results(id) ON DELETE CASCADE
            );
        """)

        # 31. Tabla maintenance_monitoring_reports (Módulo 46)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_monitoring_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER NOT NULL,
                execution_status TEXT NOT NULL,
                health_status TEXT NOT NULL,
                progress REAL NOT NULL DEFAULT 0.0,
                observations TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_id) REFERENCES maintenance_workflows(id) ON DELETE CASCADE
            );
        """)

        # 32. Tabla maintenance_alerts (Módulo 47)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monitoring_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (monitoring_id) REFERENCES maintenance_monitoring_reports(id) ON DELETE CASCADE
            );
        """)

        # 33. Tabla maintenance_supervisor_decisions (Módulo 48)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_supervisor_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                decision_type TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                priority TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES maintenance_alerts(id) ON DELETE CASCADE
            );
        """)

        # 34. Tabla maintenance_governance_evaluations (Módulo 49)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_governance_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                governance_status TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                rules_checked TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (decision_id) REFERENCES maintenance_supervisor_decisions(id) ON DELETE CASCADE
            );
        """)

        # 35. Tabla maintenance_compliance_reports (Módulo 50)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_compliance_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                governance_id INTEGER NOT NULL,
                compliant INTEGER NOT NULL,
                violations TEXT NOT NULL,
                compliance_score REAL NOT NULL DEFAULT 0.0,
                recommendation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (governance_id) REFERENCES maintenance_governance_evaluations(id) ON DELETE CASCADE
            );
        """)

        # 36. Tabla maintenance_control_optimizations (Módulo 51)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_control_optimizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compliance_id INTEGER NOT NULL,
                optimization_status TEXT NOT NULL,
                improvement_area TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.0,
                recommendation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (compliance_id) REFERENCES maintenance_compliance_reports(id) ON DELETE CASCADE
            );
        """)

        # 37. Tabla runtime_contexts (Runtime Block 01)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                status TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 38. Tabla workflow_executions (Runtime Block 02)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                context_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 39. Tabla runtime_capability_results (Runtime Block 03)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_capability_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_name TEXT NOT NULL,
                manager_name TEXT NOT NULL,
                success INTEGER NOT NULL,
                summary TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 40. Tabla autonomous_execution_cycles (Runtime Block 04)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_execution_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                status TEXT NOT NULL,
                completed_stages INTEGER DEFAULT 0,
                failed_stages INTEGER DEFAULT 0,
                total_stages INTEGER DEFAULT 9,
                success_rate REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 41. Tabla runtime_validation_reports (Runtime Block 05)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_validation_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name TEXT NOT NULL,
                status TEXT NOT NULL,
                stages_executed INTEGER DEFAULT 0,
                successful_stages INTEGER DEFAULT 0,
                failed_stages INTEGER DEFAULT 0,
                execution_time REAL DEFAULT 0.0,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 42. Tabla runtime_metrics (Runtime Block 06)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                execution_id INTEGER DEFAULT 0,
                value REAL DEFAULT 0.0,
                unit TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 43. Tabla runtime_performance_reports (Runtime Block 06)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_performance_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_executions INTEGER DEFAULT 0,
                successful_executions INTEGER DEFAULT 0,
                failed_executions INTEGER DEFAULT 0,
                average_execution_time REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0,
                most_failed_stage TEXT DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 44. Tabla runtime_learning_records (Runtime Block 08)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_execution_id INTEGER DEFAULT 0,
                source_decision_id INTEGER DEFAULT 0,
                learning_type TEXT NOT NULL,
                pattern_detected TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                impact_prediction TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 45. Tabla runtime_adaptation_recommendations (Runtime Block 08)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_adaptation_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learning_id INTEGER DEFAULT 0,
                target_area TEXT NOT NULL,
                recommended_change TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                confidence REAL DEFAULT 0.0,
                reasoning TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 46. Tabla runtime_knowledge_entries (Runtime Block 09)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_knowledge_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_type TEXT NOT NULL,
                source_learning_id INTEGER DEFAULT 0,
                pattern TEXT NOT NULL,
                description TEXT DEFAULT '',
                confidence REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 47. Tabla runtime_knowledge_queries (Runtime Block 09)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_knowledge_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_type TEXT NOT NULL,
                query_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 48. Tabla runtime_knowledge_decisions (Runtime Block 10)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_knowledge_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_knowledge_ids TEXT DEFAULT '',
                decision_type TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                supporting_patterns TEXT DEFAULT '',
                recommended_action TEXT DEFAULT '',
                reasoning TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 49. Tabla runtime_execution_plans (Runtime Block 11)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_execution_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_decision_id INTEGER DEFAULT 0,
                plan_type TEXT NOT NULL,
                steps TEXT DEFAULT '[]',
                estimated_risk TEXT DEFAULT 'low',
                confidence REAL DEFAULT 0.0,
                reasoning TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 50. Tabla runtime_plan_simulations (Runtime Block 12)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_plan_simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER DEFAULT 0,
                simulation_status TEXT NOT NULL,
                predicted_outcome TEXT DEFAULT '',
                predicted_issues TEXT DEFAULT '',
                confidence REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 51. Tabla runtime_plan_validations (Runtime Block 12)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_plan_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER DEFAULT 0,
                validation_status TEXT NOT NULL,
                risk_level TEXT DEFAULT 'low',
                checks_performed TEXT DEFAULT '[]',
                failed_checks TEXT DEFAULT '[]',
                recommendation TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 52. Tabla runtime_execution_authorizations (Runtime Block 13)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_execution_authorizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER DEFAULT 0,
                validation_id INTEGER DEFAULT 0,
                authorization_status TEXT NOT NULL,
                authorization_level TEXT DEFAULT 'normal',
                approved_conditions TEXT DEFAULT '[]',
                rejected_conditions TEXT DEFAULT '[]',
                reasoning TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 53. Tabla runtime_authorization_conditions (Runtime Block 13)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_authorization_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                authorization_id INTEGER DEFAULT 0,
                condition_name TEXT NOT NULL,
                condition_status TEXT NOT NULL,
                description TEXT DEFAULT '',
                severity TEXT DEFAULT 'info'
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

    # ----------------------------------------------------
    # Operaciones CRUD para Maintenance Decision Intelligence Layer (Módulo 30)
    # ----------------------------------------------------
    def insert_maintenance_decision(
        self,
        decision_type: Any,
        selected_strategy: Optional[str] = None,
        confidence: Optional[float] = None,
        reasoning: Optional[str] = None,
        supporting_factors: Optional[Any] = None,
        created_at: Optional[Any] = None,
    ) -> int:
        """Inserta una decisión de mantenimiento en la tabla maintenance_decisions."""
        if hasattr(decision_type, "decision_type"):
            dec = decision_type
            d_type = str(dec.decision_type)
            s_strat = str(dec.selected_strategy)
            conf = float(dec.confidence)
            reas = str(dec.reasoning)
            s_fact = json.dumps(dec.supporting_factors) if isinstance(dec.supporting_factors, list) else str(dec.supporting_factors or "[]")
            c_at = dec.created_at.isoformat() if hasattr(dec.created_at, "isoformat") else str(dec.created_at)
        elif isinstance(decision_type, dict):
            d_type = str(decision_type.get("decision_type", "default"))
            s_strat = str(decision_type.get("selected_strategy", "unknown"))
            conf = float(decision_type.get("confidence", 0.0))
            reas = str(decision_type.get("reasoning", ""))
            raw_factors = decision_type.get("supporting_factors", [])
            s_fact = json.dumps(raw_factors) if isinstance(raw_factors, list) else str(raw_factors or "[]")
            c_at = str(decision_type.get("created_at")) if decision_type.get("created_at") else None
        else:
            d_type = str(decision_type)
            s_strat = str(selected_strategy or "unknown")
            conf = float(confidence or 0.0)
            reas = str(reasoning or "")
            s_fact = json.dumps(supporting_factors) if isinstance(supporting_factors, list) else str(supporting_factors or "[]")
            c_at = str(created_at) if created_at else None

        conn = self.connect()
        cursor = conn.cursor()
        if c_at is None:
            cursor.execute(
                """
                INSERT INTO maintenance_decisions (decision_type, selected_strategy, confidence, reasoning, supporting_factors)
                VALUES (?, ?, ?, ?, ?);
                """,
                (d_type, s_strat, conf, reas, s_fact)
            )
        else:
            cursor.execute(
                """
                INSERT INTO maintenance_decisions (decision_type, selected_strategy, confidence, reasoning, supporting_factors, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (d_type, s_strat, conf, reas, s_fact, c_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_maintenance_decision(self, dec_id: int) -> Optional[dict]:
        """Obtiene una decisión de mantenimiento por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_type, selected_strategy, confidence, reasoning, supporting_factors, created_at FROM maintenance_decisions WHERE id = ?;",
            (dec_id,)
        )
        row = cursor.fetchone()
        if row:
            raw_factors = row["supporting_factors"]
            try:
                factors_list = json.loads(raw_factors) if raw_factors else []
            except Exception:
                factors_list = [raw_factors] if raw_factors else []
            return {
                "id": row["id"],
                "decision_type": row["decision_type"],
                "selected_strategy": row["selected_strategy"],
                "confidence": row["confidence"],
                "reasoning": row["reasoning"],
                "supporting_factors": factors_list,
                "created_at": str(row["created_at"]),
            }
        return None

    def get_maintenance_decisions(self) -> list:
        """Obtiene todas las decisiones de mantenimiento ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_type, selected_strategy, confidence, reasoning, supporting_factors, created_at FROM maintenance_decisions ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            raw_factors = row["supporting_factors"]
            try:
                factors_list = json.loads(raw_factors) if raw_factors else []
            except Exception:
                factors_list = [raw_factors] if raw_factors else []
            result.append({
                "id": row["id"],
                "decision_type": row["decision_type"],
                "selected_strategy": row["selected_strategy"],
                "confidence": row["confidence"],
                "reasoning": row["reasoning"],
                "supporting_factors": factors_list,
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # Operaciones CRUD para Maintenance Execution Planning Layer (Módulo 31)
    # ----------------------------------------------------
    def insert_execution_plan(
        self,
        decision_type: Any,
        strategy_type: Optional[str] = None,
        execution_steps: Optional[Any] = None,
        risk_level: Optional[str] = None,
        estimated_duration: Optional[str] = None,
        requires_approval: Optional[bool] = None,
        reasoning: Optional[str] = None,
        created_at: Optional[Any] = None,
    ) -> int:
        """Inserta un plan de ejecución de mantenimiento en la tabla maintenance_execution_plans."""
        if hasattr(decision_type, "decision_type"):
            plan = decision_type
            d_type = str(plan.decision_type)
            s_type = str(plan.strategy_type)
            steps = json.dumps(plan.execution_steps) if isinstance(plan.execution_steps, list) else str(plan.execution_steps or "[]")
            r_level = str(plan.risk_level)
            e_dur = str(plan.estimated_duration)
            req_app = 1 if getattr(plan, "requires_approval", False) else 0
            reas = str(getattr(plan, "reasoning", ""))
            c_at = plan.created_at.isoformat() if hasattr(plan.created_at, "isoformat") else str(plan.created_at)
        elif isinstance(decision_type, dict):
            d_type = str(decision_type.get("decision_type", "default"))
            s_type = str(decision_type.get("strategy_type", "unknown"))
            raw_steps = decision_type.get("execution_steps", [])
            steps = json.dumps(raw_steps) if isinstance(raw_steps, list) else str(raw_steps or "[]")
            r_level = str(decision_type.get("risk_level", "low"))
            e_dur = str(decision_type.get("estimated_duration", "0m"))
            req_app = 1 if decision_type.get("requires_approval") else 0
            reas = str(decision_type.get("reasoning", ""))
            c_at = str(decision_type.get("created_at")) if decision_type.get("created_at") else None
        else:
            d_type = str(decision_type)
            s_type = str(strategy_type or "unknown")
            steps = json.dumps(execution_steps) if isinstance(execution_steps, list) else str(execution_steps or "[]")
            r_level = str(risk_level or "low")
            e_dur = str(estimated_duration or "0m")
            req_app = 1 if requires_approval else 0
            reas = str(reasoning or "")
            c_at = str(created_at) if created_at else None

        conn = self.connect()
        cursor = conn.cursor()
        if c_at is None:
            cursor.execute(
                """
                INSERT INTO maintenance_execution_plans (decision_type, strategy_type, execution_steps, risk_level, estimated_duration, requires_approval, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (d_type, s_type, steps, r_level, e_dur, req_app, reas)
            )
        else:
            cursor.execute(
                """
                INSERT INTO maintenance_execution_plans (decision_type, strategy_type, execution_steps, risk_level, estimated_duration, requires_approval, reasoning, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (d_type, s_type, steps, r_level, e_dur, req_app, reas, c_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_execution_plan(self, plan_id: int) -> Optional[dict]:
        """Obtiene un plan de ejecución por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_type, strategy_type, execution_steps, risk_level, estimated_duration, requires_approval, reasoning, created_at FROM maintenance_execution_plans WHERE id = ?;",
            (plan_id,)
        )
        row = cursor.fetchone()
        if row:
            raw_steps = row["execution_steps"]
            try:
                steps_list = json.loads(raw_steps) if raw_steps else []
            except Exception:
                steps_list = [raw_steps] if raw_steps else []
            return {
                "id": row["id"],
                "decision_type": row["decision_type"],
                "strategy_type": row["strategy_type"],
                "execution_steps": steps_list,
                "risk_level": row["risk_level"],
                "estimated_duration": row["estimated_duration"],
                "requires_approval": bool(row["requires_approval"]),
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            }
        return None

    def get_execution_plans(self) -> list:
        """Obtiene todos los planes de ejecución ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_type, strategy_type, execution_steps, risk_level, estimated_duration, requires_approval, reasoning, created_at FROM maintenance_execution_plans ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            raw_steps = row["execution_steps"]
            try:
                steps_list = json.loads(raw_steps) if raw_steps else []
            except Exception:
                steps_list = [raw_steps] if raw_steps else []
            result.append({
                "id": row["id"],
                "decision_type": row["decision_type"],
                "strategy_type": row["strategy_type"],
                "execution_steps": steps_list,
                "risk_level": row["risk_level"],
                "estimated_duration": row["estimated_duration"],
                "requires_approval": bool(row["requires_approval"]),
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # Operaciones CRUD para Execution Validation Reports (Módulo 32)
    # ----------------------------------------------------
    def insert_validation_report(
        self,
        report: Any = None,
        plan_id: Optional[int] = None,
        valid: Optional[bool] = None,
        risk_level: Optional[str] = None,
        issues: Optional[Any] = None,
        recommendation: Optional[str] = None,
        created_at: Optional[Any] = None,
    ) -> int:
        """Inserta un reporte de validación de ejecución en la tabla execution_validation_reports."""
        if hasattr(report, "plan_id"):
            p_id = int(report.plan_id)
            v_val = 1 if report.valid else 0
            r_level = str(report.risk_level)
            iss = json.dumps(report.issues) if isinstance(report.issues, list) else str(report.issues or "[]")
            recom = str(report.recommendation)
            c_at = report.created_at.isoformat() if hasattr(report.created_at, "isoformat") else str(report.created_at)
        elif isinstance(report, dict):
            p_id = int(report.get("plan_id", 0))
            v_val = 1 if report.get("valid") else 0
            r_level = str(report.get("risk_level", "low"))
            raw_issues = report.get("issues", [])
            iss = json.dumps(raw_issues) if isinstance(raw_issues, list) else str(raw_issues or "[]")
            recom = str(report.get("recommendation", ""))
            c_at = str(report.get("created_at")) if report.get("created_at") else None
        else:
            p_id = int(plan_id or 0)
            v_val = 1 if valid else 0
            r_level = str(risk_level or "low")
            iss = json.dumps(issues) if isinstance(issues, list) else str(issues or "[]")
            recom = str(recommendation or "")
            c_at = str(created_at) if created_at else None

        conn = self.connect()
        cursor = conn.cursor()
        if c_at is None:
            cursor.execute(
                """
                INSERT INTO execution_validation_reports (plan_id, valid, risk_level, issues, recommendation)
                VALUES (?, ?, ?, ?, ?);
                """,
                (p_id, v_val, r_level, iss, recom)
            )
        else:
            cursor.execute(
                """
                INSERT INTO execution_validation_reports (plan_id, valid, risk_level, issues, recommendation, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (p_id, v_val, r_level, iss, recom, c_at)
            )
        conn.commit()
        return cursor.lastrowid

    def get_validation_report(self, report_id: int) -> Optional[dict]:
        """Obtiene un reporte de validación por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, plan_id, valid, risk_level, issues, recommendation, created_at FROM execution_validation_reports WHERE id = ?;",
            (report_id,)
        )
        row = cursor.fetchone()
        if row:
            raw_issues = row["issues"]
            try:
                issues_list = json.loads(raw_issues) if raw_issues else []
            except Exception:
                issues_list = [raw_issues] if raw_issues else []
            return {
                "id": row["id"],
                "plan_id": row["plan_id"],
                "valid": bool(row["valid"]),
                "risk_level": row["risk_level"],
                "issues": issues_list,
                "recommendation": row["recommendation"],
                "created_at": str(row["created_at"]),
            }
        return None

    def get_validation_reports(self) -> list:
        """Obtiene todos los reportes de validación ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, plan_id, valid, risk_level, issues, recommendation, created_at FROM execution_validation_reports ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            raw_issues = row["issues"]
            try:
                issues_list = json.loads(raw_issues) if raw_issues else []
            except Exception:
                issues_list = [raw_issues] if raw_issues else []
            result.append({
                "id": row["id"],
                "plan_id": row["plan_id"],
                "valid": bool(row["valid"]),
                "risk_level": row["risk_level"],
                "issues": issues_list,
                "recommendation": row["recommendation"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # Operaciones para Execution Approval Layer (Módulo 33)
    # ----------------------------------------------------
    def insert_execution_approval(self, plan_id: int, validation_id: int, approval_status: str, approved: bool, reason: str) -> int:
        """Inserta un registro de aprobación de ejecución en la base de datos."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO execution_approvals (plan_id, validation_id, approval_status, approved, reason)
            VALUES (?, ?, ?, ?, ?);
            """,
            (plan_id, validation_id, approval_status, 1 if approved else 0, reason)
        )
        conn.commit()
        return cursor.lastrowid

    def get_execution_approval(self, approval_id: int) -> dict:
        """Obtiene una aprobación por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, plan_id, validation_id, approval_status, approved, reason, created_at FROM execution_approvals WHERE id = ?;",
            (approval_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "plan_id": row["plan_id"],
                "validation_id": row["validation_id"],
                "approval_status": row["approval_status"],
                "approved": bool(row["approved"]),
                "reason": row["reason"],
                "created_at": str(row["created_at"]),
            }
        return None

    def get_execution_approvals(self) -> list:
        """Obtiene todas las aprobaciones ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, plan_id, validation_id, approval_status, approved, reason, created_at FROM execution_approvals ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "plan_id": row["plan_id"],
                "validation_id": row["validation_id"],
                "approval_status": row["approval_status"],
                "approved": bool(row["approved"]),
                "reason": row["reason"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # Operaciones CRUD para Execution Tracking (Módulo 34)
    # ----------------------------------------------------
    def insert_execution_tracking(self, approval_id: int, status: str, progress: float, message: str = "") -> int:
        """Inserta un registro de seguimiento de ejecución en execution_tracking."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO execution_tracking (approval_id, status, progress, message)
            VALUES (?, ?, ?, ?);
            """,
            (approval_id, status, progress, message)
        )
        conn.commit()
        return cursor.lastrowid

    def insert_tracking(self, approval_id: int, status: str, progress: float, message: str = "") -> int:
        """Alias para insert_execution_tracking."""
        return self.insert_execution_tracking(approval_id, status, progress, message)

    def update_execution_tracking(self, tracking_id: int, status: str, progress: float, message: str = "") -> bool:
        """Actualiza el estado, progreso y mensaje de un seguimiento de ejecución."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE execution_tracking
            SET status = ?, progress = ?, message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (status, progress, message, tracking_id)
        )
        conn.commit()
        return cursor.rowcount > 0

    def update_tracking(self, tracking_id: int, status: str, progress: float, message: str = "") -> bool:
        """Alias para update_execution_tracking."""
        return self.update_execution_tracking(tracking_id, status, progress, message)

    def get_execution_tracking(self, tracking_id: int) -> Optional[dict]:
        """Obtiene un registro de seguimiento por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, approval_id, status, progress, message, created_at, updated_at FROM execution_tracking WHERE id = ?;",
            (tracking_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "approval_id": row["approval_id"],
                "status": row["status"],
                "progress": float(row["progress"]),
                "message": row["message"] or "",
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
        return None

    def get_tracking(self, tracking_id: int) -> Optional[dict]:
        """Alias para get_execution_tracking."""
        return self.get_execution_tracking(tracking_id)

    def get_execution_trackings(self) -> list:
        """Obtiene todos los registros de seguimiento ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, approval_id, status, progress, message, created_at, updated_at FROM execution_tracking ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "approval_id": row["approval_id"],
                "status": row["status"],
                "progress": float(row["progress"]),
                "message": row["message"] or "",
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            })
        return result

    # ----------------------------------------------------
    # Operaciones CRUD para Execution Result (Módulo 35)
    # ----------------------------------------------------
    def insert_execution_result(self, tracking_id: int, result_status: str, impact: str, summary: str = "") -> int:
        """Inserta un resultado de ejecución en execution_results."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO execution_results (tracking_id, result_status, impact, summary)
            VALUES (?, ?, ?, ?);
            """,
            (tracking_id, result_status, impact, summary)
        )
        conn.commit()
        return cursor.lastrowid

    def insert_result(self, tracking_id: int, result_status: str, impact: str, summary: str = "") -> int:
        """Alias para insert_execution_result."""
        return self.insert_execution_result(tracking_id, result_status, impact, summary)

    def get_execution_result(self, result_id: int) -> Optional[dict]:
        """Obtiene un resultado de ejecución por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tracking_id, result_status, impact, summary, created_at FROM execution_results WHERE id = ?;",
            (result_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "tracking_id": row["tracking_id"],
                "result_status": row["result_status"],
                "impact": row["impact"],
                "summary": row["summary"] or "",
                "created_at": str(row["created_at"]),
            }
        return None

    def get_result(self, result_id: int) -> Optional[dict]:
        """Alias para get_execution_result."""
        return self.get_execution_result(result_id)

    def get_execution_results(self) -> list:
        """Obtiene todos los resultados de ejecución ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tracking_id, result_status, impact, summary, created_at FROM execution_results ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "tracking_id": row["tracking_id"],
                "result_status": row["result_status"],
                "impact": row["impact"],
                "summary": row["summary"] or "",
                "created_at": str(row["created_at"]),
            })
        return result

    def get_results(self) -> list:
        """Alias para get_execution_results."""
        return self.get_execution_results()

    # ----------------------------------------------------
    # Operaciones CRUD para Execution Feedback (Módulo 36)
    # ----------------------------------------------------
    def insert_execution_feedback(self, result_id: int, feedback_type: str, quality_score: float, learning_notes: str = "") -> int:
        """Inserta un registro de retroalimentación de ejecución en execution_feedback."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO execution_feedback (result_id, feedback_type, quality_score, learning_notes)
            VALUES (?, ?, ?, ?);
            """,
            (result_id, feedback_type, quality_score, learning_notes)
        )
        conn.commit()
        return cursor.lastrowid

    def insert_feedback(self, result_id: int, feedback_type: str, quality_score: float, learning_notes: str = "") -> int:
        """Alias para insert_execution_feedback."""
        return self.insert_execution_feedback(result_id, feedback_type, quality_score, learning_notes)

    def get_execution_feedback(self, feedback_id: int) -> Optional[dict]:
        """Obtiene un registro de feedback por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, result_id, feedback_type, quality_score, learning_notes, created_at FROM execution_feedback WHERE id = ?;",
            (feedback_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "result_id": row["result_id"],
                "feedback_type": row["feedback_type"],
                "quality_score": float(row["quality_score"]),
                "learning_notes": row["learning_notes"] or "",
                "created_at": str(row["created_at"]),
            }
        return None

    def get_feedback(self, feedback_id: int) -> Optional[dict]:
        """Alias para get_execution_feedback."""
        return self.get_execution_feedback(feedback_id)

    def get_execution_feedbacks(self) -> list:
        """Obtiene todos los registros de feedback ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, result_id, feedback_type, quality_score, learning_notes, created_at FROM execution_feedback ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "result_id": row["result_id"],
                "feedback_type": row["feedback_type"],
                "quality_score": float(row["quality_score"]),
                "learning_notes": row["learning_notes"] or "",
                "created_at": str(row["created_at"]),
            })
        return result

    def get_feedbacks(self) -> list:
        """Alias para get_execution_feedbacks."""
        return self.get_execution_feedbacks()

    # ----------------------------------------------------
    # MÓDULO 37: Maintenance Knowledge CRUD
    # ----------------------------------------------------
    def insert_knowledge(
        self,
        source_feedback_id: int,
        knowledge_type: str,
        description: str,
        confidence: float,
    ) -> int:
        """Inserta un registro de conocimiento extraído de mantenimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_knowledge (source_feedback_id, knowledge_type, description, confidence)
            VALUES (?, ?, ?, ?);
            """,
            (source_feedback_id, knowledge_type, description, confidence),
        )
        conn.commit()
        return cursor.lastrowid

    def get_knowledge(self, knowledge_id: int) -> Optional[dict]:
        """Obtiene un registro de conocimiento por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, source_feedback_id, knowledge_type, description, confidence, created_at FROM maintenance_knowledge WHERE id = ?;",
            (knowledge_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "source_feedback_id": row["source_feedback_id"],
                "knowledge_type": row["knowledge_type"],
                "description": row["description"] or "",
                "confidence": float(row["confidence"]),
                "created_at": str(row["created_at"]),
            }
        return None

    def get_all_knowledge(self) -> list:
        """Obtiene todo el conocimiento extraído ordenado por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, source_feedback_id, knowledge_type, description, confidence, created_at FROM maintenance_knowledge ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "source_feedback_id": row["source_feedback_id"],
                "knowledge_type": row["knowledge_type"],
                "description": row["description"] or "",
                "confidence": float(row["confidence"]),
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # MÓDULO 38: Maintenance Patterns CRUD
    # ----------------------------------------------------
    def insert_pattern(
        self,
        pattern_type: str,
        occurrences: int,
        confidence: float,
        description: str,
    ) -> int:
        """Inserta un registro de patrón de mantenimiento detectado."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_patterns (pattern_type, occurrences, confidence, description)
            VALUES (?, ?, ?, ?);
            """,
            (pattern_type, occurrences, confidence, description),
        )
        conn.commit()
        return cursor.lastrowid

    def get_pattern(self, pattern_id: int) -> Optional[dict]:
        """Obtiene un patrón de mantenimiento por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, pattern_type, occurrences, confidence, description, created_at FROM maintenance_patterns WHERE id = ?;",
            (pattern_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "pattern_type": row["pattern_type"],
                "occurrences": row["occurrences"],
                "confidence": float(row["confidence"]),
                "description": row["description"] or "",
                "created_at": str(row["created_at"]),
            }
        return None

    def get_patterns(self) -> list:
        """Obtiene todos los patrones detectados ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, pattern_type, occurrences, confidence, description, created_at FROM maintenance_patterns ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "pattern_type": row["pattern_type"],
                "occurrences": row["occurrences"],
                "confidence": float(row["confidence"]),
                "description": row["description"] or "",
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # MÓDULO 39: Maintenance Improvements CRUD
    # ----------------------------------------------------
    def insert_improvement(
        self,
        pattern_id: int,
        recommendation_type: str,
        priority: str,
        description: str,
        confidence: float,
    ) -> int:
        """Inserta una recomendación de mejora continua."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_improvements (pattern_id, recommendation_type, priority, description, confidence)
            VALUES (?, ?, ?, ?, ?);
            """,
            (pattern_id, recommendation_type, priority, description, confidence),
        )
        conn.commit()
        return cursor.lastrowid

    def get_improvement(self, improvement_id: int) -> Optional[dict]:
        """Obtiene una recomendación de mejora por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, pattern_id, recommendation_type, priority, description, confidence, created_at FROM maintenance_improvements WHERE id = ?;",
            (improvement_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "pattern_id": row["pattern_id"],
                "recommendation_type": row["recommendation_type"],
                "priority": row["priority"],
                "description": row["description"] or "",
                "confidence": float(row["confidence"]),
                "created_at": str(row["created_at"]),
            }
        return None

    def get_improvements(self) -> list:
        """Obtiene todas las recomendaciones de mejora ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, pattern_id, recommendation_type, priority, description, confidence, created_at FROM maintenance_improvements ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "pattern_id": row["pattern_id"],
                "recommendation_type": row["recommendation_type"],
                "priority": row["priority"],
                "description": row["description"] or "",
                "confidence": float(row["confidence"]),
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # MÓDULO 40: Maintenance Correlations CRUD
    # ----------------------------------------------------
    def insert_correlation(
        self,
        strategy_type: str,
        pattern_type: str,
        success_rate: float,
        sample_size: int,
        confidence: float,
        description: str,
    ) -> int:
        """Inserta un registro de correlación de inteligencia de mantenimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_correlations (strategy_type, pattern_type, success_rate, sample_size, confidence, description)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (strategy_type, pattern_type, success_rate, sample_size, confidence, description),
        )
        conn.commit()
        return cursor.lastrowid

    def get_correlation(self, correlation_id: int) -> Optional[dict]:
        """Obtiene un registro de correlación por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, strategy_type, pattern_type, success_rate, sample_size, confidence, description, created_at FROM maintenance_correlations WHERE id = ?;",
            (correlation_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "strategy_type": row["strategy_type"],
                "pattern_type": row["pattern_type"],
                "success_rate": float(row["success_rate"]),
                "sample_size": int(row["sample_size"]),
                "confidence": float(row["confidence"]),
                "description": row["description"] or "",
                "created_at": str(row["created_at"]),
            }
        return None

    def get_correlations(self) -> list:
        """Obtiene todas las correlaciones ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, strategy_type, pattern_type, success_rate, sample_size, confidence, description, created_at FROM maintenance_correlations ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "strategy_type": row["strategy_type"],
                "pattern_type": row["pattern_type"],
                "success_rate": float(row["success_rate"]),
                "sample_size": int(row["sample_size"]),
                "confidence": float(row["confidence"]),
                "description": row["description"] or "",
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # MÓDULO 41: Adaptive Decisions CRUD
    # ----------------------------------------------------
    def insert_adaptive_decision(
        self,
        correlation_id: int,
        decision_type: str,
        recommended_strategy: str,
        confidence: float,
        reasoning: str,
    ) -> int:
        """Inserta un registro de decisión adaptativa de mantenimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO adaptive_decisions (correlation_id, decision_type, recommended_strategy, confidence, reasoning)
            VALUES (?, ?, ?, ?, ?);
            """,
            (correlation_id, decision_type, recommended_strategy, confidence, reasoning),
        )
        conn.commit()
        return cursor.lastrowid

    def get_adaptive_decision(self, decision_id: int) -> Optional[dict]:
        """Obtiene un registro de decisión adaptativa por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, correlation_id, decision_type, recommended_strategy, confidence, reasoning, created_at FROM adaptive_decisions WHERE id = ?;",
            (decision_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "correlation_id": row["correlation_id"],
                "decision_type": row["decision_type"],
                "recommended_strategy": row["recommended_strategy"],
                "confidence": float(row["confidence"]),
                "reasoning": row["reasoning"] or "",
                "created_at": str(row["created_at"]),
            }
        return None

    def get_adaptive_decisions(self) -> list:
        """Obtiene todas las decisiones adaptativas ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, correlation_id, decision_type, recommended_strategy, confidence, reasoning, created_at FROM adaptive_decisions ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "correlation_id": row["correlation_id"],
                "decision_type": row["decision_type"],
                "recommended_strategy": row["recommended_strategy"],
                "confidence": float(row["confidence"]),
                "reasoning": row["reasoning"] or "",
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # MÓDULO 42: Optimization Feedback CRUD
    # ----------------------------------------------------
    def insert_optimization_feedback(
        self,
        decision_id: int,
        previous_confidence: float,
        new_confidence: float,
        improvement_score: float,
        optimization_type: str,
        summary: str,
    ) -> int:
        """Inserta un registro de retroalimentación de optimización en el ciclo continuo."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO optimization_feedback (decision_id, previous_confidence, new_confidence, improvement_score, optimization_type, summary)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (decision_id, previous_confidence, new_confidence, improvement_score, optimization_type, summary),
        )
        conn.commit()
        return cursor.lastrowid

    def get_optimization_feedback(self, feedback_id: int) -> Optional[dict]:
        """Obtiene un registro de retroalimentación de optimización por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_id, previous_confidence, new_confidence, improvement_score, optimization_type, summary, created_at FROM optimization_feedback WHERE id = ?;",
            (feedback_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "decision_id": row["decision_id"],
                "previous_confidence": float(row["previous_confidence"]),
                "new_confidence": float(row["new_confidence"]),
                "improvement_score": float(row["improvement_score"]),
                "optimization_type": row["optimization_type"],
                "summary": row["summary"] or "",
                "created_at": str(row["created_at"]),
            }
        return None

    def get_optimization_history(self) -> list:
        """Obtiene todo el historial de retroalimentación de optimización ordenado por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_id, previous_confidence, new_confidence, improvement_score, optimization_type, summary, created_at FROM optimization_feedback ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "decision_id": row["decision_id"],
                "previous_confidence": float(row["previous_confidence"]),
                "new_confidence": float(row["new_confidence"]),
                "improvement_score": float(row["improvement_score"]),
                "optimization_type": row["optimization_type"],
                "summary": row["summary"] or "",
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # Operaciones CRUD para Bloque 11 (Módulos 43-45)
    # ----------------------------------------------------

    def insert_workflow(
        self,
        decision_id: int,
        workflow_type: str,
        steps: str,
        current_step: int = 0,
        status: str = "pending",
    ) -> int:
        """Inserta un nuevo registro de flujo de trabajo de mantenimiento (Módulo 43)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_workflows (decision_id, workflow_type, steps, current_step, status)
            VALUES (?, ?, ?, ?, ?);
            """,
            (decision_id, workflow_type, steps, current_step, status),
        )
        conn.commit()
        return cursor.lastrowid

    def get_workflow(self, workflow_id: int) -> Optional[dict]:
        """Obtiene un flujo de trabajo de mantenimiento por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_id, workflow_type, steps, current_step, status, created_at FROM maintenance_workflows WHERE id = ?;",
            (workflow_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "decision_id": row["decision_id"],
                "workflow_type": row["workflow_type"],
                "steps": row["steps"],
                "current_step": int(row["current_step"]),
                "status": row["status"],
                "created_at": str(row["created_at"]),
            }
        return None

    def update_workflow_step(self, workflow_id: int, current_step: int, status: str) -> None:
        """Actualiza el paso actual y el estado de un flujo de trabajo."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE maintenance_workflows SET current_step = ?, status = ? WHERE id = ?;",
            (current_step, status, workflow_id),
        )
        conn.commit()

    def get_workflows(self) -> list:
        """Obtiene todos los flujos de trabajo registrados."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_id, workflow_type, steps, current_step, status, created_at FROM maintenance_workflows ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "decision_id": row["decision_id"],
                "workflow_type": row["workflow_type"],
                "steps": row["steps"],
                "current_step": int(row["current_step"]),
                "status": row["status"],
                "created_at": str(row["created_at"]),
            })
        return result

    def insert_policy_result(
        self,
        workflow_id: int,
        allowed: bool,
        risk_level: str,
        reasoning: str,
        violations: str = "",
    ) -> int:
        """Inserta un resultado de evaluación de política (Módulo 44)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_policy_results (workflow_id, allowed, risk_level, violations, reasoning)
            VALUES (?, ?, ?, ?, ?);
            """,
            (workflow_id, 1 if allowed else 0, risk_level, violations, reasoning),
        )
        conn.commit()
        return cursor.lastrowid

    def get_policy_result(self, policy_id: int) -> Optional[dict]:
        """Obtiene un resultado de evaluación de política por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, workflow_id, allowed, risk_level, violations, reasoning, created_at FROM maintenance_policy_results WHERE id = ?;",
            (policy_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "allowed": bool(row["allowed"]),
                "risk_level": row["risk_level"],
                "violations": row["violations"] or "",
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            }
        return None

    def get_policy_results(self) -> list:
        """Obtiene todos los resultados de políticas registrados."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, workflow_id, allowed, risk_level, violations, reasoning, created_at FROM maintenance_policy_results ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "allowed": bool(row["allowed"]),
                "risk_level": row["risk_level"],
                "violations": row["violations"] or "",
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            })
        return result

    def insert_coordination_result(
        self,
        workflow_id: int,
        policy_id: int,
        coordination_status: str,
        next_action: str,
        summary: str,
    ) -> int:
        """Inserta un resultado de coordinación autónoma (Módulo 45)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_coordination_results (workflow_id, policy_id, coordination_status, next_action, summary)
            VALUES (?, ?, ?, ?, ?);
            """,
            (workflow_id, policy_id, coordination_status, next_action, summary),
        )
        conn.commit()
        return cursor.lastrowid

    def get_coordination_result(self, coordination_id: int) -> Optional[dict]:
        """Obtiene un resultado de coordinación por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, workflow_id, policy_id, coordination_status, next_action, summary, created_at FROM maintenance_coordination_results WHERE id = ?;",
            (coordination_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "policy_id": row["policy_id"],
                "coordination_status": row["coordination_status"],
                "next_action": row["next_action"],
                "summary": row["summary"],
                "created_at": str(row["created_at"]),
            }
        return None

    def get_coordination_history(self) -> list:
        """Obtiene todo el historial de resultados de coordinación."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, workflow_id, policy_id, coordination_status, next_action, summary, created_at FROM maintenance_coordination_results ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "policy_id": row["policy_id"],
                "coordination_status": row["coordination_status"],
                "next_action": row["next_action"],
                "summary": row["summary"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Módulo 46: Maintenance Monitoring ---

    def insert_monitoring_report(
        self,
        workflow_id: int,
        execution_status: str,
        health_status: str,
        progress: float,
        observations: str,
    ) -> int:
        """Inserta un informe de monitoreo de mantenimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_monitoring_reports (workflow_id, execution_status, health_status, progress, observations)
            VALUES (?, ?, ?, ?, ?);
            """,
            (workflow_id, execution_status, health_status, float(progress), observations),
        )
        conn.commit()
        return cursor.lastrowid

    def get_monitoring_report(self, report_id: int) -> Optional[dict]:
        """Obtiene un informe de monitoreo por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, workflow_id, execution_status, health_status, progress, observations, created_at FROM maintenance_monitoring_reports WHERE id = ?;",
            (report_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "workflow_id": row["workflow_id"],
            "execution_status": row["execution_status"],
            "health_status": row["health_status"],
            "progress": float(row["progress"]),
            "observations": row["observations"],
            "created_at": str(row["created_at"]),
        }

    def get_monitoring_reports(self) -> list:
        """Obtiene todos los informes de monitoreo."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, workflow_id, execution_status, health_status, progress, observations, created_at FROM maintenance_monitoring_reports ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "execution_status": row["execution_status"],
                "health_status": row["health_status"],
                "progress": float(row["progress"]),
                "observations": row["observations"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Módulo 47: Maintenance Alerts ---

    def insert_alert(
        self,
        monitoring_id: int,
        alert_type: str,
        severity: str,
        message: str,
        recommended_action: str,
    ) -> int:
        """Inserta una alerta inteligente de mantenimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_alerts (monitoring_id, alert_type, severity, message, recommended_action)
            VALUES (?, ?, ?, ?, ?);
            """,
            (monitoring_id, alert_type, severity, message, recommended_action),
        )
        conn.commit()
        return cursor.lastrowid

    def get_alert(self, alert_id: int) -> Optional[dict]:
        """Obtiene una alerta por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, monitoring_id, alert_type, severity, message, recommended_action, created_at FROM maintenance_alerts WHERE id = ?;",
            (alert_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "monitoring_id": row["monitoring_id"],
            "alert_type": row["alert_type"],
            "severity": row["severity"],
            "message": row["message"],
            "recommended_action": row["recommended_action"],
            "created_at": str(row["created_at"]),
        }

    def get_alerts(self) -> list:
        """Obtiene todas las alertas de mantenimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, monitoring_id, alert_type, severity, message, recommended_action, created_at FROM maintenance_alerts ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "monitoring_id": row["monitoring_id"],
                "alert_type": row["alert_type"],
                "severity": row["severity"],
                "message": row["message"],
                "recommended_action": row["recommended_action"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Módulo 48: Maintenance Supervisor Decisions ---

    def insert_supervisor_decision(
        self,
        alert_id: int,
        decision_type: str,
        recommended_action: str,
        priority: str,
        reasoning: str,
    ) -> int:
        """Inserta una decisión de supervisión de mantenimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_supervisor_decisions (alert_id, decision_type, recommended_action, priority, reasoning)
            VALUES (?, ?, ?, ?, ?);
            """,
            (alert_id, decision_type, recommended_action, priority, reasoning),
        )
        conn.commit()
        return cursor.lastrowid

    def get_supervisor_decision(self, decision_id: int) -> Optional[dict]:
        """Obtiene una decisión de supervisión por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, alert_id, decision_type, recommended_action, priority, reasoning, created_at FROM maintenance_supervisor_decisions WHERE id = ?;",
            (decision_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "alert_id": row["alert_id"],
            "decision_type": row["decision_type"],
            "recommended_action": row["recommended_action"],
            "priority": row["priority"],
            "reasoning": row["reasoning"],
            "created_at": str(row["created_at"]),
        }

    def get_supervisor_decisions(self) -> list:
        """Obtiene todas las decisiones de supervisión."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, alert_id, decision_type, recommended_action, priority, reasoning, created_at FROM maintenance_supervisor_decisions ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "alert_id": row["alert_id"],
                "decision_type": row["decision_type"],
                "recommended_action": row["recommended_action"],
                "priority": row["priority"],
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Módulo 49: Maintenance Governance ---

    def insert_governance_evaluation(
        self,
        decision_id: int,
        governance_status: str,
        risk_level: str,
        rules_checked: str,
        reasoning: str,
    ) -> int:
        """Inserta una evaluación de gobernanza de mantenimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_governance_evaluations (decision_id, governance_status, risk_level, rules_checked, reasoning)
            VALUES (?, ?, ?, ?, ?);
            """,
            (decision_id, governance_status, risk_level, rules_checked, reasoning),
        )
        conn.commit()
        return cursor.lastrowid

    def get_governance_evaluation(self, evaluation_id: int) -> Optional[dict]:
        """Obtiene una evaluación de gobernanza por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_id, governance_status, risk_level, rules_checked, reasoning, created_at FROM maintenance_governance_evaluations WHERE id = ?;",
            (evaluation_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "decision_id": row["decision_id"],
            "governance_status": row["governance_status"],
            "risk_level": row["risk_level"],
            "rules_checked": row["rules_checked"],
            "reasoning": row["reasoning"],
            "created_at": str(row["created_at"]),
        }

    def get_governance_evaluations(self) -> list:
        """Obtiene todas las evaluaciones de gobernanza."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, decision_id, governance_status, risk_level, rules_checked, reasoning, created_at FROM maintenance_governance_evaluations ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "decision_id": row["decision_id"],
                "governance_status": row["governance_status"],
                "risk_level": row["risk_level"],
                "rules_checked": row["rules_checked"],
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Módulo 50: Maintenance Compliance ---

    def insert_compliance_report(
        self,
        governance_id: int,
        compliant: bool,
        violations: str,
        compliance_score: float,
        recommendation: str,
    ) -> int:
        """Inserta un informe de cumplimiento normativo."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_compliance_reports (governance_id, compliant, violations, compliance_score, recommendation)
            VALUES (?, ?, ?, ?, ?);
            """,
            (governance_id, 1 if compliant else 0, violations, float(compliance_score), recommendation),
        )
        conn.commit()
        return cursor.lastrowid

    def get_compliance_report(self, report_id: int) -> Optional[dict]:
        """Obtiene un informe de cumplimiento por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, governance_id, compliant, violations, compliance_score, recommendation, created_at FROM maintenance_compliance_reports WHERE id = ?;",
            (report_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "governance_id": row["governance_id"],
            "compliant": bool(row["compliant"]),
            "violations": row["violations"],
            "compliance_score": float(row["compliance_score"]),
            "recommendation": row["recommendation"],
            "created_at": str(row["created_at"]),
        }

    def get_compliance_reports(self) -> list:
        """Obtiene todos los informes de cumplimiento."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, governance_id, compliant, violations, compliance_score, recommendation, created_at FROM maintenance_compliance_reports ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "governance_id": row["governance_id"],
                "compliant": bool(row["compliant"]),
                "violations": row["violations"],
                "compliance_score": float(row["compliance_score"]),
                "recommendation": row["recommendation"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Módulo 51: Autonomous Control Optimization ---

    def insert_control_optimization(
        self,
        compliance_id: int,
        optimization_status: str,
        improvement_area: str,
        confidence: float,
        recommendation: str,
    ) -> int:
        """Inserta un reporte de optimización de control autónomo."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_control_optimizations (compliance_id, optimization_status, improvement_area, confidence, recommendation)
            VALUES (?, ?, ?, ?, ?);
            """,
            (compliance_id, optimization_status, improvement_area, float(confidence), recommendation),
        )
        conn.commit()
        return cursor.lastrowid

    def get_control_optimization(self, optimization_id: int) -> Optional[dict]:
        """Obtiene un reporte de optimización de control por ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, compliance_id, optimization_status, improvement_area, confidence, recommendation, created_at FROM maintenance_control_optimizations WHERE id = ?;",
            (optimization_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "compliance_id": row["compliance_id"],
            "optimization_status": row["optimization_status"],
            "improvement_area": row["improvement_area"],
            "confidence": float(row["confidence"]),
            "recommendation": row["recommendation"],
            "created_at": str(row["created_at"]),
        }

    def get_control_optimizations(self) -> list:
        """Obtiene todos los reportes de optimización de control."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, compliance_id, optimization_status, improvement_area, confidence, recommendation, created_at FROM maintenance_control_optimizations ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "compliance_id": row["compliance_id"],
                "optimization_status": row["optimization_status"],
                "improvement_area": row["improvement_area"],
                "confidence": float(row["confidence"]),
                "recommendation": row["recommendation"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Runtime Block 01: OmniLocal Core Engine ---

    def insert_runtime_context(
        self,
        operation_type: str,
        status: str,
        current_stage: str,
    ) -> int:
        """Inserta un nuevo contexto de ejecución runtime."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runtime_contexts (operation_type, status, current_stage)
            VALUES (?, ?, ?);
            """,
            (operation_type, status, current_stage),
        )
        conn.commit()
        return cursor.lastrowid

    def get_runtime_context(self, context_id: int) -> Optional[dict]:
        """Obtiene un contexto de ejecución por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, operation_type, status, current_stage, created_at FROM runtime_contexts WHERE id = ?;",
            (context_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "operation_type": row["operation_type"],
            "status": row["status"],
            "current_stage": row["current_stage"],
            "created_at": str(row["created_at"]),
        }

    def update_runtime_status(self, context_id: int, status: str, current_stage: str) -> None:
        """Actualiza el estado y la etapa actual de un contexto de ejecución."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE runtime_contexts
            SET status = ?, current_stage = ?
            WHERE id = ?;
            """,
            (status, current_stage, context_id),
        )
        conn.commit()

    def get_runtime_contexts(self) -> list:
        """Obtiene todos los contextos de ejecución ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, operation_type, status, current_stage, created_at FROM runtime_contexts ORDER BY id DESC;"
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "operation_type": row["operation_type"],
                "status": row["status"],
                "current_stage": row["current_stage"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Runtime Block 02: Workflow Execution Engine ---

    def insert_workflow_execution(
        self,
        workflow_id: str,
        context_id: int,
        status: str,
        current_stage: str,
        results: Optional[str] = None,
    ) -> int:
        """Inserta una nueva ejecución de workflow."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO workflow_executions (workflow_id, context_id, status, current_stage, results)
            VALUES (?, ?, ?, ?, ?);
            """,
            (workflow_id, context_id, status, current_stage, results),
        )
        conn.commit()
        return cursor.lastrowid

    def get_workflow_execution(self, execution_id: int) -> Optional[dict]:
        """Obtiene una ejecución de workflow por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, workflow_id, context_id, status, current_stage, results, created_at
            FROM workflow_executions WHERE id = ?;
            """,
            (execution_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "workflow_id": row["workflow_id"],
            "context_id": row["context_id"],
            "status": row["status"],
            "current_stage": row["current_stage"],
            "results": row["results"],
            "created_at": str(row["created_at"]),
        }

    def update_workflow_execution(
        self,
        execution_id: int,
        status: str,
        current_stage: str,
        results: Optional[str] = None,
    ) -> None:
        """Actualiza el estado, etapa actual y resultados de una ejecución de workflow."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE workflow_executions
            SET status = ?, current_stage = ?, results = ?
            WHERE id = ?;
            """,
            (status, current_stage, results, execution_id),
        )
        conn.commit()

    def get_workflow_executions(self) -> list:
        """Obtiene todas las ejecuciones de workflow ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, workflow_id, context_id, status, current_stage, results, created_at
            FROM workflow_executions ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "context_id": row["context_id"],
                "status": row["status"],
                "current_stage": row["current_stage"],
                "results": row["results"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Métodos Runtime Block 03: Real Capability Binding Layer ---

    def insert_capability_result(
        self,
        stage_name: str,
        manager_name: str,
        success: bool,
        summary: str,
        data: Optional[str] = None,
    ) -> int:
        """Inserta un nuevo resultado de ejecución de capability binding."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runtime_capability_results (stage_name, manager_name, success, summary, data)
            VALUES (?, ?, ?, ?, ?);
            """,
            (stage_name, manager_name, 1 if success else 0, summary, data),
        )
        conn.commit()
        return cursor.lastrowid

    def get_capability_result(self, result_id: int) -> Optional[dict]:
        """Obtiene un resultado de capability binding por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, stage_name, manager_name, success, summary, data, created_at
            FROM runtime_capability_results WHERE id = ?;
            """,
            (result_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "stage_name": row["stage_name"],
            "manager_name": row["manager_name"],
            "success": bool(row["success"]),
            "summary": row["summary"],
            "data": row["data"],
            "created_at": str(row["created_at"]),
        }

    def get_capability_results(self) -> list:
        """Obtiene todos los resultados de capability binding ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, stage_name, manager_name, success, summary, data, created_at
            FROM runtime_capability_results ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "stage_name": row["stage_name"],
                "manager_name": row["manager_name"],
                "success": bool(row["success"]),
                "summary": row["summary"],
                "data": row["data"],
                "created_at": str(row["created_at"]),
            })
        return result


    def insert_autonomous_cycle(
        self,
        workflow_id: str,
        status: str = "running",
        completed_stages: int = 0,
        failed_stages: int = 0,
        total_stages: int = 9,
        success_rate: float = 0.0,
    ) -> int:
        """Inserta un nuevo ciclo de ejecución autónoma y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO autonomous_execution_cycles (workflow_id, status, completed_stages, failed_stages, total_stages, success_rate)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (workflow_id, status, completed_stages, failed_stages, total_stages, success_rate),
        )
        conn.commit()
        return cursor.lastrowid

    def update_autonomous_cycle(
        self,
        cycle_id: int,
        status: str,
        completed_stages: int,
        failed_stages: int,
        total_stages: int,
        success_rate: float,
    ) -> bool:
        """Actualiza el estado y métricas de un ciclo de ejecución autónoma."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE autonomous_execution_cycles
            SET status = ?, completed_stages = ?, failed_stages = ?, total_stages = ?, success_rate = ?
            WHERE id = ?;
            """,
            (status, completed_stages, failed_stages, total_stages, success_rate, cycle_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_autonomous_cycle(self, cycle_id: int) -> Optional[dict]:
        """Obtiene un ciclo de ejecución autónoma por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, workflow_id, status, completed_stages, failed_stages, total_stages, success_rate, created_at
            FROM autonomous_execution_cycles WHERE id = ?;
            """,
            (cycle_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "workflow_id": row["workflow_id"],
            "status": row["status"],
            "completed_stages": row["completed_stages"],
            "failed_stages": row["failed_stages"],
            "total_stages": row["total_stages"],
            "success_rate": row["success_rate"],
            "created_at": str(row["created_at"]),
        }

    def get_autonomous_cycles(self) -> list:
        """Obtiene todos los ciclos de ejecución autónoma ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, workflow_id, status, completed_stages, failed_stages, total_stages, success_rate, created_at
            FROM autonomous_execution_cycles ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "workflow_id": row["workflow_id"],
                "status": row["status"],
                "completed_stages": row["completed_stages"],
                "failed_stages": row["failed_stages"],
                "total_stages": row["total_stages"],
                "success_rate": row["success_rate"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # CRUD para Runtime Validation Reports (Runtime Block 05)
    # ----------------------------------------------------
    def insert_runtime_validation_report(
        self,
        scenario_name: str,
        status: str,
        stages_executed: int = 0,
        successful_stages: int = 0,
        failed_stages: int = 0,
        execution_time: float = 0.0,
        summary: str = "",
        created_at: Optional[str] = None
    ) -> int:
        """Inserta un reporte de validación runtime y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_validation_reports (
                scenario_name, status, stages_executed, successful_stages, failed_stages, execution_time, summary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (scenario_name, status, stages_executed, successful_stages, failed_stages, execution_time, summary, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_runtime_validation_report(self, report_id: int) -> Optional[dict]:
        """Obtiene un reporte de validación runtime por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, scenario_name, status, stages_executed, successful_stages, failed_stages, execution_time, summary, created_at
            FROM runtime_validation_reports WHERE id = ?;
            """,
            (report_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "scenario_name": row["scenario_name"],
            "status": row["status"],
            "stages_executed": row["stages_executed"],
            "successful_stages": row["successful_stages"],
            "failed_stages": row["failed_stages"],
            "execution_time": row["execution_time"],
            "summary": row["summary"],
            "created_at": str(row["created_at"]),
        }

    def get_runtime_validation_reports(self) -> list:
        """Obtiene todos los reportes de validación runtime ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, scenario_name, status, stages_executed, successful_stages, failed_stages, execution_time, summary, created_at
            FROM runtime_validation_reports ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "scenario_name": row["scenario_name"],
                "status": row["status"],
                "stages_executed": row["stages_executed"],
                "successful_stages": row["successful_stages"],
                "failed_stages": row["failed_stages"],
                "execution_time": row["execution_time"],
                "summary": row["summary"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # CRUD para Runtime Observability (Runtime Block 06)
    # ----------------------------------------------------
    def insert_runtime_metric(
        self,
        metric_type: str,
        workflow_id: str,
        execution_id: int = 0,
        value: float = 0.0,
        unit: str = "",
        created_at: Optional[str] = None
    ) -> int:
        """Inserta una métrica runtime en runtime_metrics y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_metrics (
                metric_type, workflow_id, execution_id, value, unit, created_at
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            (metric_type, workflow_id, execution_id, value, unit, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_runtime_metrics(self) -> list:
        """Obtiene todas las métricas runtime registradas ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, metric_type, workflow_id, execution_id, value, unit, created_at
            FROM runtime_metrics ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "metric_type": row["metric_type"],
                "workflow_id": row["workflow_id"],
                "execution_id": row["execution_id"],
                "value": row["value"],
                "unit": row["unit"],
                "created_at": str(row["created_at"]),
            })
        return result

    def insert_performance_report(
        self,
        total_executions: int = 0,
        successful_executions: int = 0,
        failed_executions: int = 0,
        average_execution_time: float = 0.0,
        success_rate: float = 0.0,
        most_failed_stage: str = "none",
        created_at: Optional[str] = None
    ) -> int:
        """Inserta un reporte de rendimiento runtime en runtime_performance_reports."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_performance_reports (
                total_executions, successful_executions, failed_executions, average_execution_time, success_rate, most_failed_stage, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (total_executions, successful_executions, failed_executions, average_execution_time, success_rate, most_failed_stage, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_performance_reports(self) -> list:
        """Obtiene todos los reportes de rendimiento runtime ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, total_executions, successful_executions, failed_executions, average_execution_time, success_rate, most_failed_stage, created_at
            FROM runtime_performance_reports ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "total_executions": row["total_executions"],
                "successful_executions": row["successful_executions"],
                "failed_executions": row["failed_executions"],
                "average_execution_time": row["average_execution_time"],
                "success_rate": row["success_rate"],
                "most_failed_stage": row["most_failed_stage"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # CRUD para Runtime Learning & Adaptation (Runtime Block 08)
    # ----------------------------------------------------
    def insert_learning_record(
        self,
        learning_type: str,
        pattern_detected: str,
        source_execution_id: int = 0,
        source_decision_id: int = 0,
        confidence: float = 0.0,
        impact_prediction: str = "",
        created_at: Optional[str] = None
    ) -> int:
        """Inserta un registro de aprendizaje runtime y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_learning_records (
                source_execution_id, source_decision_id, learning_type, pattern_detected, confidence, impact_prediction, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (source_execution_id, source_decision_id, learning_type, pattern_detected, confidence, impact_prediction, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_learning_records(self) -> list:
        """Obtiene todos los registros de aprendizaje ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, source_execution_id, source_decision_id, learning_type, pattern_detected, confidence, impact_prediction, created_at
            FROM runtime_learning_records ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "source_execution_id": row["source_execution_id"],
                "source_decision_id": row["source_decision_id"],
                "learning_type": row["learning_type"],
                "pattern_detected": row["pattern_detected"],
                "confidence": row["confidence"],
                "impact_prediction": row["impact_prediction"],
                "created_at": str(row["created_at"]),
            })
        return result

    def insert_adaptation(
        self,
        learning_id: int,
        target_area: str,
        recommended_change: str,
        priority: str = "medium",
        confidence: float = 0.0,
        reasoning: str = "",
        created_at: Optional[str] = None
    ) -> int:
        """Inserta una recomendación de adaptación runtime y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_adaptation_recommendations (
                learning_id, target_area, recommended_change, priority, confidence, reasoning, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (learning_id, target_area, recommended_change, priority, confidence, reasoning, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_adaptations(self) -> list:
        """Obtiene todas las recomendaciones de adaptación ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, learning_id, target_area, recommended_change, priority, confidence, reasoning, created_at
            FROM runtime_adaptation_recommendations ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "learning_id": row["learning_id"],
                "target_area": row["target_area"],
                "recommended_change": row["recommended_change"],
                "priority": row["priority"],
                "confidence": row["confidence"],
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # CRUD para Runtime Knowledge Consolidation (Runtime Block 09)
    # ----------------------------------------------------
    def insert_knowledge_entry(
        self,
        knowledge_type: str,
        pattern: str,
        source_learning_id: int = 0,
        description: str = "",
        confidence: float = 0.0,
        usage_count: int = 0,
        created_at: Optional[str] = None
    ) -> int:
        """Inserta una entrada de conocimiento consolidado y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_knowledge_entries (
                knowledge_type, source_learning_id, pattern, description, confidence, usage_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (knowledge_type, source_learning_id, pattern, description, confidence, usage_count, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_knowledge_entries(self) -> list:
        """Obtiene todas las entradas de conocimiento ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, knowledge_type, source_learning_id, pattern, description, confidence, usage_count, created_at
            FROM runtime_knowledge_entries ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "knowledge_type": row["knowledge_type"],
                "source_learning_id": row["source_learning_id"],
                "pattern": row["pattern"],
                "description": row["description"],
                "confidence": row["confidence"],
                "usage_count": row["usage_count"],
                "created_at": str(row["created_at"]),
            })
        return result

    def insert_knowledge_query(
        self,
        query_type: str,
        query_value: str,
        created_at: Optional[str] = None
    ) -> int:
        """Inserta un registro de consulta de conocimiento y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_knowledge_queries (
                query_type, query_value, created_at
            ) VALUES (?, ?, ?);
            """,
            (query_type, query_value, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_knowledge_queries(self) -> list:
        """Obtiene todas las consultas de conocimiento registradas."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, query_type, query_value, created_at
            FROM runtime_knowledge_queries ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "query_type": row["query_type"],
                "query_value": row["query_value"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # CRUD para Knowledge-Augmented Decision Layer (Runtime Block 10)
    # ----------------------------------------------------
    def insert_knowledge_decision(
        self,
        decision_type: str,
        source_knowledge_ids: str = "",
        confidence: float = 0.0,
        supporting_patterns: str = "",
        recommended_action: str = "",
        reasoning: str = "",
        created_at: Optional[str] = None
    ) -> int:
        """Inserta un informe de decisión basada en conocimiento y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_knowledge_decisions (
                decision_type, source_knowledge_ids, confidence, supporting_patterns, recommended_action, reasoning, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (decision_type, source_knowledge_ids, confidence, supporting_patterns, recommended_action, reasoning, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_knowledge_decision(self, decision_id: int) -> Optional[dict]:
        """Obtiene una decisión de conocimiento por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, source_knowledge_ids, decision_type, confidence, supporting_patterns, recommended_action, reasoning, created_at
            FROM runtime_knowledge_decisions WHERE id = ?;
            """,
            (decision_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "source_knowledge_ids": row["source_knowledge_ids"],
            "decision_type": row["decision_type"],
            "confidence": row["confidence"],
            "supporting_patterns": row["supporting_patterns"],
            "recommended_action": row["recommended_action"],
            "reasoning": row["reasoning"],
            "created_at": str(row["created_at"]),
        }

    def get_knowledge_decisions(self) -> list:
        """Obtiene todas las decisiones de conocimiento ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, source_knowledge_ids, decision_type, confidence, supporting_patterns, recommended_action, reasoning, created_at
            FROM runtime_knowledge_decisions ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "source_knowledge_ids": row["source_knowledge_ids"],
                "decision_type": row["decision_type"],
                "confidence": row["confidence"],
                "supporting_patterns": row["supporting_patterns"],
                "recommended_action": row["recommended_action"],
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            })
        return result

    # ----------------------------------------------------
    # CRUD para Autonomous Planning Layer (Runtime Block 11)
    # ----------------------------------------------------
    def insert_execution_plan(
        self,
        plan_type: str,
        source_decision_id: int = 0,
        steps: str = "[]",
        estimated_risk: str = "low",
        confidence: float = 0.0,
        reasoning: str = "",
        created_at: Optional[str] = None
    ) -> int:
        """Inserta un plan de ejecución autónomo y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        if created_at is None:
            created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO runtime_execution_plans (
                source_decision_id, plan_type, steps, estimated_risk, confidence, reasoning, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (source_decision_id, plan_type, steps, estimated_risk, confidence, reasoning, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    def get_execution_plan(self, plan_id: int) -> Optional[dict]:
        """Obtiene un plan de ejecución por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, source_decision_id, plan_type, steps, estimated_risk, confidence, reasoning, created_at
            FROM runtime_execution_plans WHERE id = ?;
            """,
            (plan_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "source_decision_id": row["source_decision_id"],
            "plan_type": row["plan_type"],
            "steps": row["steps"],
            "estimated_risk": row["estimated_risk"],
            "confidence": row["confidence"],
            "reasoning": row["reasoning"],
            "created_at": str(row["created_at"]),
        }

    def get_execution_plans(self) -> list:
        """Obtiene todos los planes de ejecución ordenados por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, source_decision_id, plan_type, steps, estimated_risk, confidence, reasoning, created_at
            FROM runtime_execution_plans ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "source_decision_id": row["source_decision_id"],
                "plan_type": row["plan_type"],
                "steps": row["steps"],
                "estimated_risk": row["estimated_risk"],
                "confidence": row["confidence"],
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Runtime Block 12: Plan Validation & Simulation CRUD ---

    def insert_plan_simulation(
        self,
        plan_id: int,
        simulation_status: str,
        predicted_outcome: str = "",
        predicted_issues: str = "",
        confidence: float = 0.0
    ) -> int:
        """Inserta una simulación de plan en runtime_plan_simulations y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runtime_plan_simulations
            (plan_id, simulation_status, predicted_outcome, predicted_issues, confidence)
            VALUES (?, ?, ?, ?, ?);
            """,
            (plan_id, simulation_status, predicted_outcome, predicted_issues, confidence)
        )
        conn.commit()
        return cursor.lastrowid

    def get_plan_simulation(self, simulation_id: int) -> Optional[dict]:
        """Obtiene una simulación de plan por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, plan_id, simulation_status, predicted_outcome, predicted_issues, confidence, created_at
            FROM runtime_plan_simulations WHERE id = ?;
            """,
            (simulation_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "plan_id": row["plan_id"],
            "simulation_status": row["simulation_status"],
            "predicted_outcome": row["predicted_outcome"],
            "predicted_issues": row["predicted_issues"],
            "confidence": row["confidence"],
            "created_at": str(row["created_at"]),
        }

    def get_plan_simulations(self) -> list:
        """Obtiene todas las simulaciones de planes ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, plan_id, simulation_status, predicted_outcome, predicted_issues, confidence, created_at
            FROM runtime_plan_simulations ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "plan_id": row["plan_id"],
                "simulation_status": row["simulation_status"],
                "predicted_outcome": row["predicted_outcome"],
                "predicted_issues": row["predicted_issues"],
                "confidence": row["confidence"],
                "created_at": str(row["created_at"]),
            })
        return result

    def insert_plan_validation(
        self,
        plan_id: int,
        validation_status: str,
        risk_level: str = "low",
        checks_performed: str = "[]",
        failed_checks: str = "[]",
        recommendation: str = ""
    ) -> int:
        """Inserta una validación de plan en runtime_plan_validations y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runtime_plan_validations
            (plan_id, validation_status, risk_level, checks_performed, failed_checks, recommendation)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (plan_id, validation_status, risk_level, checks_performed, failed_checks, recommendation)
        )
        conn.commit()
        return cursor.lastrowid

    def get_plan_validation(self, validation_id: int) -> Optional[dict]:
        """Obtiene un reporte de validación de plan por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, plan_id, validation_status, risk_level, checks_performed, failed_checks, recommendation, created_at
            FROM runtime_plan_validations WHERE id = ?;
            """,
            (validation_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "plan_id": row["plan_id"],
            "validation_status": row["validation_status"],
            "risk_level": row["risk_level"],
            "checks_performed": row["checks_performed"],
            "failed_checks": row["failed_checks"],
            "recommendation": row["recommendation"],
            "created_at": str(row["created_at"]),
        }

    def get_plan_validations(self) -> list:
        """Obtiene todas las validaciones de planes ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, plan_id, validation_status, risk_level, checks_performed, failed_checks, recommendation, created_at
            FROM runtime_plan_validations ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "plan_id": row["plan_id"],
                "validation_status": row["validation_status"],
                "risk_level": row["risk_level"],
                "checks_performed": row["checks_performed"],
                "failed_checks": row["failed_checks"],
                "recommendation": row["recommendation"],
                "created_at": str(row["created_at"]),
            })
        return result

    # --- Runtime Block 13: Execution Authorization CRUD ---

    def insert_execution_authorization(
        self,
        plan_id: int,
        validation_id: int,
        authorization_status: str,
        authorization_level: str = "normal",
        approved_conditions: str = "[]",
        rejected_conditions: str = "[]",
        reasoning: str = ""
    ) -> int:
        """Inserta un registro de autorización en runtime_execution_authorizations y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runtime_execution_authorizations
            (plan_id, validation_id, authorization_status, authorization_level, approved_conditions, rejected_conditions, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (plan_id, validation_id, authorization_status, authorization_level, approved_conditions, rejected_conditions, reasoning)
        )
        conn.commit()
        return cursor.lastrowid

    def get_execution_authorization(self, authorization_id: int) -> Optional[dict]:
        """Obtiene un registro de autorización por su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, plan_id, validation_id, authorization_status, authorization_level, approved_conditions, rejected_conditions, reasoning, created_at
            FROM runtime_execution_authorizations WHERE id = ?;
            """,
            (authorization_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "plan_id": row["plan_id"],
            "validation_id": row["validation_id"],
            "authorization_status": row["authorization_status"],
            "authorization_level": row["authorization_level"],
            "approved_conditions": row["approved_conditions"],
            "rejected_conditions": row["rejected_conditions"],
            "reasoning": row["reasoning"],
            "created_at": str(row["created_at"]),
        }

    def get_execution_authorizations(self) -> list:
        """Obtiene todas las autorizaciones ordenadas por ID descendente."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, plan_id, validation_id, authorization_status, authorization_level, approved_conditions, rejected_conditions, reasoning, created_at
            FROM runtime_execution_authorizations ORDER BY id DESC;
            """
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "plan_id": row["plan_id"],
                "validation_id": row["validation_id"],
                "authorization_status": row["authorization_status"],
                "authorization_level": row["authorization_level"],
                "approved_conditions": row["approved_conditions"],
                "rejected_conditions": row["rejected_conditions"],
                "reasoning": row["reasoning"],
                "created_at": str(row["created_at"]),
            })
        return result

    def insert_authorization_condition(
        self,
        authorization_id: int,
        condition_name: str,
        condition_status: str,
        description: str = "",
        severity: str = "info"
    ) -> int:
        """Inserta una condición de autorización en runtime_authorization_conditions y devuelve su ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runtime_authorization_conditions
            (authorization_id, condition_name, condition_status, description, severity)
            VALUES (?, ?, ?, ?, ?);
            """,
            (authorization_id, condition_name, condition_status, description, severity)
        )
        conn.commit()
        return cursor.lastrowid

    def get_authorization_conditions(self, authorization_id: int) -> list:
        """Obtiene las condiciones asociadas a un ID de autorización."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, authorization_id, condition_name, condition_status, description, severity
            FROM runtime_authorization_conditions WHERE authorization_id = ?;
            """,
            (authorization_id,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "authorization_id": row["authorization_id"],
                "condition_name": row["condition_name"],
                "condition_status": row["condition_status"],
                "description": row["description"],
                "severity": row["severity"],
            })
        return result


    def close(self) -> None:
        """Cierra la conexión activa con la base de datos."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
