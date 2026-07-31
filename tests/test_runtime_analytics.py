import unittest
from omnilocal_runtime.observability.analytics import RuntimeAnalytics


class TestRuntimeAnalytics(unittest.TestCase):

    def test_calculate_success_rate(self):
        self.assertEqual(RuntimeAnalytics.calculate_success_rate(10, 8), 80.0)
        self.assertEqual(RuntimeAnalytics.calculate_success_rate(0, 0), 0.0)
        self.assertEqual(RuntimeAnalytics.calculate_success_rate(3, 3), 100.0)
        self.assertEqual(RuntimeAnalytics.calculate_success_rate(4, 1), 25.0)

    def test_calculate_average_execution_time(self):
        times = [1.2, 2.4, 0.6]
        self.assertEqual(RuntimeAnalytics.calculate_average_execution_time(times), 1.4)
        self.assertEqual(RuntimeAnalytics.calculate_average_execution_time([]), 0.0)

    def test_identify_failed_stages(self):
        stage_details = [
            {"stage_name": "validation", "status": "failed"},
            {"stage_name": "validation", "status": "failed"},
            {"stage_name": "feedback_generation", "status": "failed"},
            {"stage_name": "memory_analysis", "status": "completed"},
        ]
        most_failed = RuntimeAnalytics.identify_failed_stages(stage_details)
        self.assertEqual(most_failed, "validation")

    def test_identify_failed_stages_none(self):
        stage_details = [
            {"stage_name": "memory_analysis", "status": "completed"},
            {"stage_name": "validation", "status": "completed"},
        ]
        most_failed = RuntimeAnalytics.identify_failed_stages(stage_details)
        self.assertEqual(most_failed, "none")

    def test_generate_summary(self):
        summary = RuntimeAnalytics.generate_summary(10, 80.0, 1.25, "validation")
        self.assertIn("10 ejecuciones", summary)
        self.assertIn("80.0%", summary)
        self.assertIn("validation", summary)

        empty_summary = RuntimeAnalytics.generate_summary(0, 0.0, 0.0, "none")
        self.assertIn("No se han registrado", empty_summary)


if __name__ == "__main__":
    unittest.main()
