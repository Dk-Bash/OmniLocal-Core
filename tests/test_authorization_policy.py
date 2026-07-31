import unittest
from omnilocal_runtime.authorization.policy import RuntimeAuthorizationPolicy


class TestAuthorizationPolicy(unittest.TestCase):

    def test_check_validation_status_approved(self):
        val_report = {"validation_status": "approved", "failed_checks": []}
        cond = RuntimeAuthorizationPolicy.check_validation_status(val_report)
        self.assertEqual(cond.condition_status, "passed")
        self.assertEqual(cond.condition_name, "validation_status_check")

    def test_check_validation_status_approved_with_warnings(self):
        val_report = {"validation_status": "approved_with_warnings", "failed_checks": ["minor_delay"]}
        cond = RuntimeAuthorizationPolicy.check_validation_status(val_report)
        self.assertEqual(cond.condition_status, "warning")

    def test_check_validation_status_rejected(self):
        val_report = {"validation_status": "rejected", "failed_checks": ["syntax_error"]}
        cond = RuntimeAuthorizationPolicy.check_validation_status(val_report)
        self.assertEqual(cond.condition_status, "failed")

    def test_check_risk_threshold_low_medium_high_critical(self):
        c_low = RuntimeAuthorizationPolicy.check_risk_threshold("low")
        self.assertEqual(c_low.condition_status, "passed")

        c_med = RuntimeAuthorizationPolicy.check_risk_threshold("medium")
        self.assertEqual(c_med.condition_status, "passed")

        c_high = RuntimeAuthorizationPolicy.check_risk_threshold("high")
        self.assertEqual(c_high.condition_status, "warning")

        c_crit = RuntimeAuthorizationPolicy.check_risk_threshold("critical")
        self.assertEqual(c_crit.condition_status, "failed")

    def test_check_confidence_threshold(self):
        c_high = RuntimeAuthorizationPolicy.check_confidence_threshold(0.88)
        self.assertEqual(c_high.condition_status, "passed")

        c_mid = RuntimeAuthorizationPolicy.check_confidence_threshold(0.60)
        self.assertEqual(c_mid.condition_status, "warning")

        c_low = RuntimeAuthorizationPolicy.check_confidence_threshold(0.30)
        self.assertEqual(c_low.condition_status, "failed")

    def test_check_mandatory_conditions(self):
        val_report_ok = {"failed_checks": []}
        c_ok = RuntimeAuthorizationPolicy.check_mandatory_conditions(val_report_ok)
        self.assertEqual(c_ok.condition_status, "passed")

        val_report_fail = {"failed_checks": ["critical_safety_violation"]}
        c_fail = RuntimeAuthorizationPolicy.check_mandatory_conditions(val_report_fail)
        self.assertEqual(c_fail.condition_status, "failed")

    def test_evaluate_policy_full(self):
        val_report = {
            "validation_status": "approved",
            "risk_level": "low",
            "failed_checks": []
        }
        conditions = RuntimeAuthorizationPolicy.evaluate_policy(val_report, confidence_score=0.90)
        self.assertEqual(len(conditions), 4)
        self.assertTrue(all(c.condition_status == "passed" for c in conditions))


if __name__ == "__main__":
    unittest.main()
