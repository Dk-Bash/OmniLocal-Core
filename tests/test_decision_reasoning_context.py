import unittest
from omnilocal_runtime.knowledge.models import RuntimeKnowledgeEntry
from omnilocal_runtime.decision_intelligence.knowledge_context import RuntimeKnowledgeContextBuilder
from omnilocal_runtime.decision_intelligence.reasoning import KnowledgeAwareReasoningEngine


class TestDecisionReasoningContext(unittest.TestCase):

    def test_calculate_relevance(self):
        entry = RuntimeKnowledgeEntry(
            knowledge_type="failure_pattern",
            pattern="timeout_error",
            confidence=0.80
        )

        metrics = {"error_rate": 0.12, "avg_latency": 450}
        relevance = RuntimeKnowledgeContextBuilder.calculate_relevance(entry, metrics)
        self.assertGreater(relevance, 0.80)

    def test_build_context(self):
        entries = [
            RuntimeKnowledgeEntry(
                id=1,
                knowledge_type="performance_pattern",
                pattern="fast_cache",
                confidence=0.90
            )
        ]
        metrics = {"avg_latency": 100, "error_rate": 0.0}
        context = RuntimeKnowledgeContextBuilder.build_context(entries, metrics)

        self.assertIsNotNone(context)
        self.assertIn("fast_cache", context.matched_patterns)
        self.assertGreaterEqual(context.relevance_score, 0.5)

    def test_evaluate_with_context_fallback(self):
        metrics = {"error_rate": 0.25, "avg_latency": 800}
        validations = [{"success": False, "details": "Validation failed"}]
        context = {"matched_patterns": '[{"id": 1, "pattern": "severe_failure", "knowledge_type": "failure_pattern"}]', "relevance_score": 0.90}

        report = KnowledgeAwareReasoningEngine.evaluate_with_context(metrics, validations, context)
        self.assertEqual(report.decision_type, "fallback")
        self.assertIn("fallback", report.reasoning)
        self.assertIn("severe_failure", report.supporting_patterns)

    def test_calculate_decision_confidence(self):
        conf = KnowledgeAwareReasoningEngine.calculate_decision_confidence(
            metrics_confidence=0.85,
            knowledge_relevance=0.90,
            pattern_count=2
        )
        self.assertGreaterEqual(conf, 0.85)
        self.assertLessEqual(conf, 0.99)


if __name__ == "__main__":
    unittest.main()
