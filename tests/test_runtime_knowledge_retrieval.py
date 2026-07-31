import unittest
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.knowledge.manager import RuntimeKnowledgeManager
from omnilocal_runtime.knowledge.retrieval import RuntimeKnowledgeRetriever


class TestRuntimeKnowledgeRetrieval(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.knowledge_mgr = RuntimeKnowledgeManager(db_manager=self.db)

        # Poblar con conocimientos de prueba
        self.knowledge_mgr.create_knowledge(
            knowledge_type="failure_pattern",
            pattern="validation_timeout",
            description="Fallo recurrente por timeout en etapa de validación",
            confidence=0.88
        )

        self.knowledge_mgr.create_knowledge(
            knowledge_type="performance_pattern",
            pattern="workflow_fast_path",
            description="Ruta rápida de ejecución optimizada para pipelines simples",
            confidence=0.92
        )

        self.knowledge_mgr.create_knowledge(
            knowledge_type="optimization_pattern",
            pattern="memory_cache_hit",
            description="Estrategia de caché en memoria de alta eficiencia",
            confidence=0.65
        )

    def test_search_knowledge_by_type(self):
        entries = self.knowledge_mgr.get_knowledge_entries()
        failures = RuntimeKnowledgeRetriever.search_knowledge(entries, query_type="knowledge_type", query_value="failure_pattern")
        self.assertGreaterEqual(len(failures), 1)
        self.assertTrue(all("failure_pattern" in str(f.get("knowledge_type") if isinstance(f, dict) else f.knowledge_type) for f in failures))

    def test_find_related_patterns(self):
        entries = self.knowledge_mgr.get_knowledge_entries()
        related = RuntimeKnowledgeRetriever.find_related_patterns(entries, pattern_name="memory cache")
        self.assertGreaterEqual(len(related), 1)

    def test_get_high_confidence_patterns(self):
        entries = self.knowledge_mgr.get_knowledge_entries()
        high_conf = RuntimeKnowledgeRetriever.get_high_confidence_patterns(entries, min_confidence=0.80)
        self.assertGreaterEqual(len(high_conf), 2)
        for item in high_conf:
            conf = item.get("confidence") if isinstance(item, dict) else item.confidence
            self.assertGreaterEqual(conf, 0.80)

    def test_query_knowledge_manager_and_logging(self):
        query_res = self.knowledge_mgr.query_knowledge(query_type="high_confidence", query_value="0.80")
        self.assertIn("results_count", query_res)
        self.assertGreaterEqual(query_res["results_count"], 2)

        queries_log = self.knowledge_mgr.get_knowledge_queries()
        self.assertGreaterEqual(len(queries_log), 1)
        self.assertEqual(queries_log[0]["query_type"], "high_confidence")


if __name__ == "__main__":
    unittest.main()
