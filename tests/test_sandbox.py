import unittest

from agent.tools.sandbox import _repo_slug, classify_jest_result


class SandboxClassificationTests(unittest.TestCase):
    def test_failed_test_is_reproduced_before_failed_suite(self):
        result = {
            "numFailedTests": 1,
            "numFailedTestSuites": 1,
            "numPassedTests": 0,
            "testResults": [{"failureMessage": "expected 50, received 60"}],
        }
        classification, message, _summary = classify_jest_result(result)
        self.assertEqual(classification, "reproduced")
        self.assertIn("received 60", message)

    def test_failed_suite_without_failed_test_is_broken(self):
        classification, _message, _summary = classify_jest_result(
            {"numFailedTests": 0, "numFailedTestSuites": 1, "numPassedTests": 0}
        )
        self.assertEqual(classification, "repro_broken")

    def test_passed_test_is_not_reproduced(self):
        classification, _message, _summary = classify_jest_result(
            {"numFailedTests": 0, "numFailedTestSuites": 0, "numPassedTests": 1}
        )
        self.assertEqual(classification, "not_reproduced")

    def test_empty_result_is_infrastructure_error(self):
        classification, _message, _summary = classify_jest_result({})
        self.assertEqual(classification, "infra_error")

    def test_parses_https_repo_url(self):
        self.assertEqual(
            _repo_slug("https://github.com/verma359211/bug-triage-target-app.git"),
            "verma359211/bug-triage-target-app",
        )


if __name__ == "__main__":
    unittest.main()

