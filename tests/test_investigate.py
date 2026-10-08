import unittest

from agent.nodes.investigate import failed_generation_text


class FakeModelError(Exception):
    def __init__(self, body):
        self.body = body


class InvestigationRecoveryTests(unittest.TestCase):
    def test_extracts_rejected_plain_text_conclusion(self):
        error = FakeModelError(
            {"error": {"failed_generation": "The inspected calculation rounds each line."}}
        )
        self.assertEqual(
            failed_generation_text(error),
            "The inspected calculation rounds each line.",
        )

    def test_unrelated_error_is_not_recovered(self):
        self.assertEqual(failed_generation_text(RuntimeError("network")), "")


if __name__ == "__main__":
    unittest.main()
