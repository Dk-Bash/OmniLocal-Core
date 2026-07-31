import unittest
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.validation.manager import RuntimeValidationManager
from omnilocal_runtime.validation.models import RuntimeValidationReport


class TestRuntimeValidation(unittest.TestCase):

    def setUp(self):
        self.db = SQLiteManager()
        self.db.create_tables()
        self.manager = RuntimeValidationManager(db_manager=self.db)

    def test_run_default_validation(self):
        report = self.manager.run_validation()
        self.assertIsNotNone(report.id)
        self.assertEqual(report.scenario_name, "memory_optimization_success")
        self.assertEqual(report.status, "passed")
        self.assertEqual(report.stages_executed, 9)
        self.assertEqual(report.successful_stages, 9)
        self.assertEqual(report.failed_stages, 0)

    def test_report_persistence_and_retrieval(self):
        report = self.manager.execute_scenario("memory_optimization_success")
        report_id = report.id

        retrieved = self.manager.get_report(report_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, report_id)
        self.assertEqual(retrieved.scenario_name, "memory_optimization_success")
        self.assertEqual(retrieved.status, "passed")

        reports_list = self.manager.get_reports()
        self.assertTrue(any(r["id"] == report_id for r in reports_list))

    def test_run_all_validations(self):
        reports = self.manager.run_all_validations()
        self.assertEqual(len(reports), 3)

        scenarios_run = [r.scenario_name for r in reports]
        self.assertIn("memory_optimization_success", scenarios_run)
        self.assertIn("capability_failure_handling", scenarios_run)
        self.assertIn("partial_execution", scenarios_run)


if __name__ == "__main__":
    unittest.main()
