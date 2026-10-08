import unittest

from agent.graph import route_after_confidence, route_after_interpretation
from agent.nodes.interpret_result import interpret_result


class ConfidenceRoutingTests(unittest.TestCase):
    def test_low_confidence_reinvestigates_before_cap(self):
        self.assertEqual(
            route_after_confidence(
                {"layer_guess": "backend", "confidence": "low", "investigate_rounds": 2}
            ),
            "investigate",
        )

    def test_low_confidence_reproduces_at_investigation_cap(self):
        self.assertEqual(
            route_after_confidence(
                {"layer_guess": "backend", "confidence": "low", "investigate_rounds": 3}
            ),
            "write_repro",
        )

    def test_high_confidence_writes_reproduction(self):
        self.assertEqual(
            route_after_confidence(
                {"layer_guess": "backend", "confidence": "high", "investigate_rounds": 1}
            ),
            "write_repro",
        )

    def test_frontend_reports_without_looping(self):
        self.assertEqual(
            route_after_confidence(
                {"layer_guess": "frontend", "confidence": "low", "investigate_rounds": 1}
            ),
            "report",
        )

    def test_interpretation_route_uses_bounded_next_step(self):
        self.assertEqual(route_after_interpretation({"next_step": "run_repro"}), "run_repro")
        self.assertEqual(route_after_interpretation({"next_step": "unexpected"}), "report")


class ReproductionRoutingTests(unittest.TestCase):
    def test_not_reproduced_reinvestigates_before_cap(self):
        result = interpret_result(
            {
                "repro_result": {"classification": "not_reproduced"},
                "investigate_rounds": 1,
                "not_reproduced_count": 0,
                "repro_attempts": 1,
            }
        )
        self.assertEqual(result["next_step"], "investigate")

    def test_not_reproduced_reports_at_round_cap(self):
        result = interpret_result(
            {
                "repro_result": {"classification": "not_reproduced"},
                "investigate_rounds": 3,
                "not_reproduced_count": 2,
                "repro_attempts": 3,
            }
        )
        self.assertEqual(result["status"], "not_reproduced")
        self.assertEqual(result["next_step"], "report")

    def test_broken_test_is_rewritten_at_most_three_attempts(self):
        retry = interpret_result(
            {
                "repro_result": {"classification": "repro_broken"},
                "investigate_rounds": 1,
                "repro_attempts": 2,
            }
        )
        exhausted = interpret_result(
            {
                "repro_result": {"classification": "repro_broken"},
                "investigate_rounds": 1,
                "repro_attempts": 3,
            }
        )
        self.assertEqual(retry["next_step"], "write_repro")
        self.assertEqual(exhausted["status"], "repro_broken")

    def test_infrastructure_error_retries_once(self):
        retry = interpret_result(
            {
                "repro_result": {"classification": "infra_error"},
                "infra_retries": 0,
                "repro_attempts": 1,
            }
        )
        exhausted = interpret_result(
            {
                "repro_result": {"classification": "infra_error"},
                "infra_retries": 1,
                "repro_attempts": 2,
            }
        )
        self.assertEqual(retry["next_step"], "run_repro")
        self.assertEqual(exhausted["status"], "could_not_run")


if __name__ == "__main__":
    unittest.main()
