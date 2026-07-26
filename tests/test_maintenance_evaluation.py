import os
import tempfile
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_audit.manager import AuditManager
from maintenance_evaluation.manager import OutcomeEvaluationManager
from maintenance_evaluation.models import OutcomeEvaluation


class TestMaintenanceEvaluation:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

        self.audit_manager = AuditManager(db_manager=self.db_manager)
        self.eval_manager = OutcomeEvaluationManager(audit_manager=self.audit_manager)

        yield

        self.db_manager.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_positive_outcome_evaluation(self):
        """Prueba que un evento con status 'completed' resulte en result_type 'positive' y score 0.9."""
        event = self.audit_manager.record_event(
            event_type="simulation_run",
            source_layer="memory_simulation",
            description="Simulation finished cleanly",
            status="completed",
        )

        evaluation = self.eval_manager.evaluate_event(event.id)

        assert isinstance(evaluation, OutcomeEvaluation)
        assert evaluation.id is not None and evaluation.id > 0
        assert evaluation.event_id == event.id
        assert evaluation.result_type == "positive"
        assert evaluation.score == 0.9
        assert "favorable" in evaluation.summary.lower()

    def test_blocked_outcome_evaluation(self):
        """Prueba que un evento con status 'blocked' resulte en result_type 'neutral' y score 0.5."""
        event = self.audit_manager.record_event(
            event_type="governance_review",
            source_layer="memory_governance",
            description="High risk task held",
            status="blocked",
        )

        evaluation = self.eval_manager.evaluate_event(event.id)

        assert isinstance(evaluation, OutcomeEvaluation)
        assert evaluation.event_id == event.id
        assert evaluation.result_type == "neutral"
        assert evaluation.score == 0.5
        assert "blocked" in evaluation.summary.lower()

    def test_failed_outcome_evaluation(self):
        """Prueba que un evento con status 'failed' resulte en result_type 'negative' y score 0.1."""
        event = self.audit_manager.record_event(
            event_type="maintenance_attempt",
            source_layer="memory_maintenance",
            description="Routine execution failed due to lock",
            status="failed",
        )

        evaluation = self.eval_manager.evaluate_event(event.id)

        assert isinstance(evaluation, OutcomeEvaluation)
        assert evaluation.event_id == event.id
        assert evaluation.result_type == "negative"
        assert evaluation.score == 0.1
        assert "failed" in evaluation.summary.lower()

    def test_integrity_no_side_effects(self):
        """Verifica que evaluar resultados no altere memorias, sesiones, conocimiento ni auditorías."""
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES ('Memory A', 'fact', 0.7);"
        )
        cursor.execute(
            "INSERT INTO context_sessions (session_name, active) VALUES ('Session 1', 1);"
        )
        cursor.execute(
            "INSERT INTO knowledge_nodes (name, node_type, description) VALUES ('Node 1', 'concept', 'Desc 1');"
        )
        conn.commit()

        event = self.audit_manager.record_event(
            event_type="test_event",
            source_layer="memory_test",
            description="Testing side effects",
            status="completed",
        )

        initial_memories = self.db_manager.count_memories()
        initial_sessions = self.db_manager.count_sessions()

        cursor.execute("SELECT COUNT(*) FROM knowledge_nodes;")
        initial_knowledge = cursor.fetchone()[0]

        initial_audits = len(self.audit_manager.get_history())

        # Evaluar resultado
        self.eval_manager.evaluate_event(event.id)

        final_memories = self.db_manager.count_memories()
        final_sessions = self.db_manager.count_sessions()

        cursor.execute("SELECT COUNT(*) FROM knowledge_nodes;")
        final_knowledge = cursor.fetchone()[0]

        final_audits = len(self.audit_manager.get_history())

        # Verificar que la cantidad de datos permanece intacta
        assert initial_memories == final_memories == 1
        assert initial_sessions == final_sessions == 1
        assert initial_knowledge == final_knowledge == 1
        assert initial_audits == final_audits == 1
