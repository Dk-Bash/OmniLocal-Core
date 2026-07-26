import os
import tempfile
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_audit.manager import AuditManager
from maintenance_audit.models import AuditEvent


class TestMaintenanceAudit:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

        self.audit_manager = AuditManager(db_manager=self.db_manager)

        yield

        self.db_manager.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_record_event(self):
        """Prueba que un evento de auditoría sea registrado con un ID válido y datos exactos."""
        event = self.audit_manager.record_event(
            event_type="simulation_completed",
            source_layer="memory_simulation",
            description="Simulation executed successfully",
            status="completed",
        )

        assert isinstance(event, AuditEvent)
        assert event.id is not None and event.id > 0
        assert event.event_type == "simulation_completed"
        assert event.source_layer == "memory_simulation"
        assert event.description == "Simulation executed successfully"
        assert event.status == "completed"

    def test_get_history_ordering_and_count(self):
        """Prueba la recuperación del historial completo con múltiples eventos en orden cronológico."""
        e1 = self.audit_manager.record_event(
            event_type="recommendation_generated",
            source_layer="memory_maintenance",
            description="Duplicate memory detected",
            status="info",
        )
        e2 = self.audit_manager.record_event(
            event_type="plan_created",
            source_layer="memory_planning",
            description="Maintenance plan structured",
            status="pending",
        )
        e3 = self.audit_manager.record_event(
            event_type="governance_evaluated",
            source_layer="memory_governance",
            description="High risk task flag",
            status="requires_review",
        )

        history = self.audit_manager.get_history()

        assert len(history) == 3
        assert history[0].id == e1.id
        assert history[1].id == e2.id
        assert history[2].id == e3.id
        assert history[0].event_type == "recommendation_generated"
        assert history[1].event_type == "plan_created"
        assert history[2].event_type == "governance_evaluated"

    def test_integrity_no_side_effects(self):
        """Verifica que registrar eventos de auditoría no altere memorias, sesiones ni conocimiento."""
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES ('Test memory', 'fact', 0.8);"
        )
        cursor.execute(
            "INSERT INTO context_sessions (session_name, active) VALUES ('Test Session', 1);"
        )
        cursor.execute(
            "INSERT INTO knowledge_nodes (name, node_type, description) VALUES ('Node A', 'concept', 'Desc A');"
        )
        conn.commit()

        initial_memories = self.db_manager.count_memories()
        initial_sessions = self.db_manager.count_sessions()

        cursor.execute("SELECT COUNT(*) FROM knowledge_nodes;")
        initial_knowledge = cursor.fetchone()[0]

        # Registrar múltiples eventos de auditoría
        self.audit_manager.record_event("test_type_1", "layer_1", "desc 1", "ok")
        self.audit_manager.record_event("test_type_2", "layer_2", "desc 2", "ok")

        # Verificar que la cantidad de memorias, sesiones y conocimiento permanece idéntica
        final_memories = self.db_manager.count_memories()
        final_sessions = self.db_manager.count_sessions()

        cursor.execute("SELECT COUNT(*) FROM knowledge_nodes;")
        final_knowledge = cursor.fetchone()[0]

        assert initial_memories == final_memories == 1
        assert initial_sessions == final_sessions == 1
        assert initial_knowledge == final_knowledge == 1
