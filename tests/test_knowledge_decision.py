import unittest
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.knowledge.manager import RuntimeKnowledgeManager
from omnilocal_runtime.decision_intelligence.manager import KnowledgeAwareDecisionManager


class TestKnowledgeDecision(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.knowledge_mgr = RuntimeKnowledgeManager(db_manager=self.db)
        self.decision_mgr = KnowledgeAwareDecisionManager(db_manager=self.db, knowledge_manager=self.knowledge_mgr)

    def test_generate_decision_with_knowledge(self):
        # Poblar con conocimientos previos
        self.knowledge_mgr.create_knowledge(
            knowledge_type="failure_pattern",
            pattern="validation_instability",
            description="Fallo de validación detectado previamente",
            confidence=0.85
        )

        decision = self.decision_mgr.generate_decision(
            current_metrics={"error_rate": 0.08, "avg_latency": 320},
            validation_reports=[{"success": True, "details": "ok"}]
        )

        self.assertIsNotNone(decision.id)
        self.assertIn(decision.decision_type, ["investigate", "optimize", "continue", "fallback"])
        self.assertGreater(decision.confidence, 0.5)
        self.assertIn("validation_instability", decision.supporting_patterns)

        decisions_list = self.decision_mgr.get_decisions()
        self.assertTrue(any(d["id"] == decision.id for d in decisions_list))

    def test_get_decision_by_id(self):
        decision = self.decision_mgr.generate_decision(
            current_metrics={"error_rate": 0.0, "avg_latency": 100},
            validation_reports=[{"success": True}]
        )

        fetched = self.decision_mgr.get_decision(decision.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], decision.id)
        self.assertEqual(fetched["decision_type"], decision.decision_type)

    def test_non_mutation_rule(self):
        # Asegurar que generar una decisión NO altera la cantidad de entradas de conocimiento ni memorias pasadas
        knowledge_before = len(self.knowledge_mgr.get_knowledge_entries())
        self.decision_mgr.generate_decision(current_metrics={"error_rate": 0.0, "avg_latency": 100})
        knowledge_after = len(self.knowledge_mgr.get_knowledge_entries())
        self.assertEqual(knowledge_before, knowledge_after)


if __name__ == "__main__":
    unittest.main()
