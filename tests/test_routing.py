import unittest

from agent.graph import route_after_confidence


class ConfidenceRoutingTests(unittest.TestCase):
    def test_low_confidence_reinvestigates_before_cap(self):
        self.assertEqual(
            route_after_confidence(
                {"layer_guess": "backend", "confidence": "low", "investigate_rounds": 2}
            ),
            "investigate",
        )

    def test_low_confidence_reports_at_cap(self):
        self.assertEqual(
            route_after_confidence(
                {"layer_guess": "backend", "confidence": "low", "investigate_rounds": 3}
            ),
            "report",
        )

    def test_high_confidence_reports(self):
        self.assertEqual(
            route_after_confidence(
                {"layer_guess": "backend", "confidence": "high", "investigate_rounds": 1}
            ),
            "report",
        )

    def test_frontend_reports_without_looping(self):
        self.assertEqual(
            route_after_confidence(
                {"layer_guess": "frontend", "confidence": "low", "investigate_rounds": 1}
            ),
            "report",
        )


if __name__ == "__main__":
    unittest.main()

