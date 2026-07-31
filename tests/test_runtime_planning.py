import unittest
import json
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.knowledge.manager import RuntimeKnowledgeManager
from omnilocal_runtime.decision_intelligence.manager import KnowledgeAwareDecisionManager
from omnilocal_runtime.planning.manager import RuntimePlanningManager


class TestRuntimePlanning(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.knowledge_mgr = RuntimeKnowledgeManager(db_manager=self.db)
        self.decision_mgr = KnowledgeAwareDecisionManager(db_manager=self.db, knowledge_manager=self.knowledge_mgr)
        self.planning_mgr = RuntimePlanningManager(
            db_manager=self.db,
            decision_manager=self.decision_mgr,
            knowledge_manager=self.knowledge_mgr
        )

    def test_create_plan_flow(self):
        # 1. Crear decision previa
        decision = self.decision_mgr.generate_decision(current_metrics={"error_rate": 0.0, "avg_latency": 100})

        # 2. Generar plan a partir de esa decision
        plan = self.planning_mgr.create_plan(source_decision_id=decision.id)

        self.assertIsNotNone(plan.id)
        self.assertEqual(plan.source_decision_id, decision.id)
        self.assertIn(plan.plan_type, ["optimization_plan", "recovery_plan", "investigation_plan", "fallback_plan"])

        # Verificar deserialización de pasos
        steps = json.loads(plan.steps)
        self.assertIsInstance(steps, list)
        self.assertGreaterEqual(len(steps), 1)

        # Verificar ordenamiento de pasos
        for idx, step in enumerate(steps, start=1):
            self.assertEqual(step["step_number"], idx)

    def test_get_plan_by_id_and_all_plans(self):
        plan = self.planning_mgr.create_plan(current_metrics={"error_rate": 0.08, "avg_latency": 350})

        fetched = self.planning_mgr.get_plan(plan.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], plan.id)
        self.assertEqual(fetched["plan_type"], plan.plan_type)

        all_plans = self.planning_mgr.get_plans()
        self.assertTrue(any(p["id"] == plan.id for p in all_plans))

    def test_invariance_no_modification_rule(self):
        # Regla: La generación de planes NO modifica decisiones pasadas ni entradas de conocimiento
        decisions_before = len(self.decision_mgr.get_decisions())
        knowledge_before = len(self.knowledge_mgr.get_knowledge_entries())

        self.planning_mgr.create_plan(current_metrics={"error_rate": 0.0, "avg_latency": 100})

        decisions_after = len(self.decision_mgr.get_decisions())
        knowledge_after = len(self.knowledge_mgr.get_knowledge_entries())

        # No se borraron ni alteraron las decisiones o conocimientos existentes
        self.assertGreaterEqual(decisions_after, decisions_before)
        self.assertEqual(knowledge_after, knowledge_before)


if __name__ == "__main__":
    unittest.main()
