import unittest
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.validation.scenarios import ScenarioManager


class TestRuntimeScenarios(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.sc_mgr = ScenarioManager(db_manager=self.db)

    def test_scenario_memory_optimization_success(self):
        report = self.sc_mgr.execute_scenario("memory_optimization_success")
        self.assertEqual(report.scenario_name, "memory_optimization_success")
        self.assertEqual(report.status, "passed")
        self.assertEqual(report.successful_stages, 9)
        self.assertEqual(report.failed_stages, 0)
        self.assertGreaterEqual(report.execution_time, 0.0)

    def test_scenario_capability_failure_handling(self):
        report = self.sc_mgr.execute_scenario("capability_failure_handling")
        self.assertEqual(report.scenario_name, "capability_failure_handling")
        self.assertEqual(report.status, "passed")
        self.assertGreater(report.failed_stages, 0)
        self.assertIn("fallo fue capturado", report.summary.lower())

    def test_scenario_partial_execution(self):
        report = self.sc_mgr.execute_scenario("partial_execution")
        self.assertEqual(report.scenario_name, "partial_execution")
        self.assertEqual(report.status, "passed")
        self.assertEqual(report.failed_stages, 2)
        self.assertEqual(report.successful_stages, 7)

    def test_unknown_scenario_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.sc_mgr.execute_scenario("non_existent_scenario")


if __name__ == "__main__":
    unittest.main()
