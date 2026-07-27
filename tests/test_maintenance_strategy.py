import os
import tempfile
import pytest
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.manager import MaintenanceManager
from memory_planning.manager import MaintenancePlanningManager
from memory_priority.manager import MemoryPriorityManager
from maintenance_audit.manager import AuditManager
from maintenance_evaluation.manager import OutcomeEvaluationManager
from maintenance_intelligence.manager import MaintenanceIntelligenceManager
from maintenance_strategy.manager import MaintenanceStrategyManager
from maintenance_strategy.models import StrategyRecommendation


class TestMaintenanceStrategy:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

        self.memory_manager = MemoryManager(db_manager=self.db_manager)
        self.integrity_manager = MemoryIntegrityManager(
            memory_manager=self.memory_manager,
            db_manager=self.db_manager
        )
        self.maintenance_manager = MaintenanceManager(
            integrity_manager=self.integrity_manager
        )
        self.planning_manager = MaintenancePlanningManager(
            maintenance_manager=self.maintenance_manager
        )
        self.priority_manager = MemoryPriorityManager(
            planning_manager=self.planning_manager
        )

        self.audit_manager = AuditManager(db_manager=self.db_manager)
        self.eval_manager = OutcomeEvaluationManager(
            audit_manager=self.audit_manager
        )
        self.intel_manager = MaintenanceIntelligenceManager(
            eval_manager=self.eval_manager
        )

        self.strategy_manager = MaintenanceStrategyManager(
            priority_manager=self.priority_manager,
            intelligence_manager=self.intel_manager
        )

        yield

        self.db_manager.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_empty_strategy(self):
        """Prueba que sin tareas en el sistema la estrategia retornada sea una lista vacía."""
        recs = self.strategy_manager.generate_strategy()
        assert isinstance(recs, list)
        assert len(recs) == 0

    def test_critical_high_medium_tasks_strategy(self):
        """Prueba mapeo de niveles (critical, high, medium) a (immediate, soon, planned)."""
        # 1. Duplicado -> priority medium -> planned (0.5)
        self.memory_manager.save_memory("Memoria Idéntica", "semantic", 0.5)
        self.memory_manager.save_memory("Memoria Idéntica", "semantic", 0.5)

        # 2. Memoria vacía -> priority critical -> immediate (1.0)
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("", "episodic", 0.5)
        )

        # 3. Importancia inválida -> priority high -> soon (0.8)
        cursor.execute(
            "INSERT INTO memories (content, memory_type, importance) VALUES (?, ?, ?);",
            ("Valida pero importancia fuera de rango", "semantic", 3.0)
        )
        conn.commit()

        recs = self.strategy_manager.generate_strategy()
        assert len(recs) == 3

        rec_map = {r.task_type: r for r in recs}

        # Tarea crítica (empty_memory_review)
        assert "empty_memory_review" in rec_map
        crit = rec_map["empty_memory_review"]
        assert crit.recommended_priority == "immediate"
        assert crit.expected_benefit == 1.0

        # Tarea alta (importance_fix)
        assert "importance_fix" in rec_map
        high = rec_map["importance_fix"]
        assert high.recommended_priority == "soon"
        assert high.expected_benefit == 0.8

        # Tarea media (duplicate_review)
        assert "duplicate_review" in rec_map
        med = rec_map["duplicate_review"]
        assert med.recommended_priority == "planned"
        assert med.expected_benefit == 0.5

    def test_low_priority_task_strategy(self):
        """Prueba que una tarea de baja prioridad se asigne a deferred con expected_benefit=0.2."""
        class DummyTask:
            id = 999
            task_type = "routine_cleanup"
            priority_level = "low"

        class DummyReport:
            tasks = [DummyTask()]

        class DummyPriorityManager:
            def prioritize(self):
                return DummyReport()

        dummy_strat = MaintenanceStrategyManager(
            priority_manager=DummyPriorityManager(),
            intelligence_manager=self.intel_manager
        )

        recs = dummy_strat.generate_strategy()
        assert len(recs) == 1
        rec = recs[0]
        assert rec.task_type == "routine_cleanup"
        assert rec.recommended_priority == "deferred"
        assert rec.expected_benefit == 0.2

    def test_integrity_no_side_effects(self):
        """Verifica que la generación de la estrategia no modifique la base de datos ni memorias."""
        self.memory_manager.save_memory("Contenido de prueba", "fact", 0.7)

        initial_memories = self.db_manager.count_memories()
        initial_audits = len(self.audit_manager.get_history())
        initial_evals = self.db_manager.count_outcome_events()

        recs = self.strategy_manager.generate_strategy()

        final_memories = self.db_manager.count_memories()
        final_audits = len(self.audit_manager.get_history())
        final_evals = self.db_manager.count_outcome_events()

        assert initial_memories == final_memories
        assert initial_audits == final_audits
        assert initial_evals == final_evals
