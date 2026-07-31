import unittest
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.learning.manager import RuntimeLearningManager
from omnilocal_runtime.knowledge.manager import RuntimeKnowledgeManager
from omnilocal_runtime.knowledge.consolidation import RuntimeKnowledgeConsolidator


class TestRuntimeKnowledge(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.learning_mgr = RuntimeLearningManager(db_manager=self.db)
        self.knowledge_mgr = RuntimeKnowledgeManager(db_manager=self.db, learning_manager=self.learning_mgr)

    def test_create_knowledge_entry(self):
        entry = self.knowledge_mgr.create_knowledge(
            knowledge_type="failure_pattern",
            pattern="validation_instability",
            source_learning_id=1,
            description="Patrón recurrente de fallos de validación",
            confidence=0.85,
            usage_count=3
        )

        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.knowledge_type, "failure_pattern")
        self.assertEqual(entry.pattern, "validation_instability")
        self.assertEqual(entry.confidence, 0.85)

        entries = self.knowledge_mgr.get_knowledge_entries()
        self.assertTrue(any(e["id"] == entry.id for e in entries))

    def test_consolidate_knowledge(self):
        # Crear aprendizajes previos
        self.learning_mgr.generate_learning_record(
            learning_type="failure_pattern",
            pattern_detected="memory_leak",
            confidence=0.80,
            impact_prediction="Prevenir fugas de memoria"
        )

        result = self.knowledge_mgr.consolidate_knowledge()
        self.assertIn("source_learnings_processed", result)
        self.assertIn("consolidated_entries_created", result)
        self.assertGreaterEqual(result["consolidated_entries_created"], 1)

    def test_merge_similar_patterns(self):
        raw_list = [
            {"knowledge_type": "failure_pattern", "pattern": "timeout", "confidence": 0.70, "usage_count": 1},
            {"knowledge_type": "failure_pattern", "pattern": "timeout", "confidence": 0.80, "usage_count": 2},
        ]

        merged = RuntimeKnowledgeConsolidator.merge_similar_patterns(raw_list)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].pattern, "timeout")
        self.assertEqual(merged[0].usage_count, 3)
        self.assertGreater(merged[0].confidence, 0.75)

    def test_historical_invariance(self):
        # Asegurar que la consolidación de conocimiento no altera ni elimina datos de aprendizaje u observabilidad
        learnings_before = len(self.learning_mgr.get_learning_records())
        self.knowledge_mgr.consolidate_knowledge()
        learnings_after = len(self.learning_mgr.get_learning_records())
        self.assertEqual(learnings_before, learnings_after)


if __name__ == "__main__":
    unittest.main()
