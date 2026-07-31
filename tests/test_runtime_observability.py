import unittest
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.observability.manager import RuntimeObservabilityManager
from omnilocal_runtime.validation.manager import RuntimeValidationManager


class TestRuntimeObservability(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.obs_mgr = RuntimeObservabilityManager(db_manager=self.db)
        self.val_mgr = RuntimeValidationManager(db_manager=self.db)

    def test_record_metric(self):
        metric = self.obs_mgr.record_metric(
            metric_type="latency",
            workflow_id="memory_optimization",
            execution_id=1,
            value=0.145,
            unit="seconds"
        )
        self.assertIsNotNone(metric.id)
        self.assertEqual(metric.metric_type, "latency")
        self.assertEqual(metric.workflow_id, "memory_optimization")
        self.assertEqual(metric.value, 0.145)

        metrics = self.obs_mgr.get_metrics()
        self.assertTrue(any(m["id"] == metric.id for m in metrics))

    def test_generate_performance_report(self):
        # Generar un par de validaciones para tener datos históricos
        self.val_mgr.execute_scenario("memory_optimization_success")
        self.val_mgr.execute_scenario("capability_failure_handling")

        perf_report = self.obs_mgr.generate_performance_report()
        self.assertIsNotNone(perf_report.id)
        self.assertGreaterEqual(perf_report.total_executions, 2)
        self.assertGreaterEqual(perf_report.successful_executions, 1)

        reports = self.obs_mgr.get_reports()
        self.assertTrue(any(r["id"] == perf_report.id for r in reports))

    def test_historical_executions_unmodified(self):
        # Verificar que la generación de reportes no altera el conteo ni estado de las ejecuciones previas
        val_before = self.val_mgr.get_reports()
        count_before = len(val_before)

        self.obs_mgr.generate_performance_report()

        val_after = self.val_mgr.get_reports()
        count_after = len(val_after)

        self.assertEqual(count_before, count_after)


if __name__ == "__main__":
    unittest.main()
