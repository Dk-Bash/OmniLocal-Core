import os
import tempfile
import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_audit.manager import AuditManager
from maintenance_evaluation.manager import OutcomeEvaluationManager
from maintenance_intelligence.manager import MaintenanceIntelligenceManager
from maintenance_intelligence.models import MaintenanceIntelligenceReport


class TestMaintenanceIntelligence:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

        self.audit_manager = AuditManager(db_manager=self.db_manager)
        self.eval_manager = OutcomeEvaluationManager(audit_manager=self.audit_manager)
        self.intel_manager = MaintenanceIntelligenceManager(eval_manager=self.eval_manager)

        yield

        self.db_manager.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_empty_database_report(self):
        """Prueba que un reporte sobre base de datos vacía retorne métricas en cero/None."""
        report = self.intel_manager.generate_report()

        assert isinstance(report, MaintenanceIntelligenceReport)
        assert report.total_events == 0
        assert report.completed_events == 0
        assert report.blocked_events == 0
        assert report.failed_events == 0
        assert report.average_score == 0.0
        assert report.most_common_result is None

    def test_full_distribution_and_average(self):
        """Prueba la generación de métricas y promedio con eventos positive, neutral y negative."""
        # Evento 1: completed -> positive (0.9)
        e1 = self.audit_manager.record_event(
            event_type="sim_run",
            source_layer="memory_sim",
            description="Run A",
            status="completed",
        )
        self.eval_manager.evaluate_event(e1.id)

        # Evento 2: blocked -> neutral (0.5)
        e2 = self.audit_manager.record_event(
            event_type="gov_review",
            source_layer="memory_gov",
            description="Run B",
            status="blocked",
        )
        self.eval_manager.evaluate_event(e2.id)

        # Evento 3: failed -> negative (0.1)
        e3 = self.audit_manager.record_event(
            event_type="maint_exec",
            source_layer="memory_maint",
            description="Run C",
            status="failed",
        )
        self.eval_manager.evaluate_event(e3.id)

        report = self.intel_manager.generate_report()

        assert report.total_events == 3
        assert report.completed_events == 1
        assert report.blocked_events == 1
        assert report.failed_events == 1
        assert pytest.approx(report.average_score, 0.01) == 0.5
        assert report.most_common_result in ["positive", "neutral", "negative"]

    def test_most_common_result(self):
        """Prueba que se identifique correctamente el resultado más común."""
        # Crear 2 eventos completados (positive) y 1 bloqueado (neutral)
        e1 = self.audit_manager.record_event("type1", "layer1", "desc1", "completed")
        e2 = self.audit_manager.record_event("type2", "layer1", "desc2", "completed")
        e3 = self.audit_manager.record_event("type3", "layer1", "desc3", "blocked")

        self.eval_manager.evaluate_event(e1.id)
        self.eval_manager.evaluate_event(e2.id)
        self.eval_manager.evaluate_event(e3.id)

        report = self.intel_manager.generate_report()

        assert report.total_events == 3
        assert report.completed_events == 2
        assert report.blocked_events == 1
        assert report.failed_events == 0
        assert report.most_common_result == "positive"
        assert pytest.approx(report.average_score, 0.01) == round((0.9 + 0.9 + 0.5) / 3, 4)

    def test_integrity_no_side_effects(self):
        """Verifica que generar reportes analíticos no altere evaluaciones, auditorías, memorias, sesiones ni conocimiento."""
        conn = self.db_manager.connect()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES ('Memory Alpha', 'fact', 0.8);"
        )
        cursor.execute(
            "INSERT INTO context_sessions (session_name, active) VALUES ('Session Delta', 1);"
        )
        cursor.execute(
            "INSERT INTO knowledge_nodes (name, node_type, description) VALUES ('Node Alpha', 'concept', 'Desc Alpha');"
        )
        conn.commit()

        event = self.audit_manager.record_event(
            event_type="test_event",
            source_layer="memory_test",
            description="Testing side effects",
            status="completed",
        )
        self.eval_manager.evaluate_event(event.id)

        initial_memories = self.db_manager.count_memories()
        initial_sessions = self.db_manager.count_sessions()

        cursor.execute("SELECT COUNT(*) FROM knowledge_nodes;")
        initial_knowledge = cursor.fetchone()[0]

        initial_audits = len(self.audit_manager.get_history())
        initial_evals = self.db_manager.count_outcome_events()

        # Generar reporte analítico
        report = self.intel_manager.generate_report()
        assert report.total_events == 1

        final_memories = self.db_manager.count_memories()
        final_sessions = self.db_manager.count_sessions()

        cursor.execute("SELECT COUNT(*) FROM knowledge_nodes;")
        final_knowledge = cursor.fetchone()[0]

        final_audits = len(self.audit_manager.get_history())
        final_evals = self.db_manager.count_outcome_events()

        # Comprobar estado inalterado
        assert initial_memories == final_memories == 1
        assert initial_sessions == final_sessions == 1
        assert initial_knowledge == final_knowledge == 1
        assert initial_audits == final_audits == 1
        assert initial_evals == final_evals == 1
