import unittest

from agent.graph import route_after_diagnosis, route_after_plan, route_after_repro
from agent.nodes.assess_repro import assess_repro


class GraphRoutingTests(unittest.TestCase):
    def test_frontend_skips_reproduction(self):
        self.assertEqual(route_after_plan({"layer_guess": "frontend"}), "load_evidence")

    def test_backend_runs_reproduction_first(self):
        self.assertEqual(route_after_plan({"layer_guess": "backend"}), "run_repro")

    def test_diagnosis_expands_evidence_only_once(self):
        self.assertEqual(
            route_after_diagnosis({"requested_files": ["src/more.js"], "evidence_rounds": 1}),
            "load_evidence",
        )
        self.assertEqual(
            route_after_diagnosis({"requested_files": ["src/more.js"], "evidence_rounds": 2}),
            "report",
        )

    def test_mismatched_failure_routes_to_one_repair(self):
        self.assertEqual(
            route_after_diagnosis(
                {"next_step": "repair_repro", "requested_files": [], "evidence_rounds": 1}
            ),
            "repair_repro",
        )

    def test_unknown_repro_route_falls_back_to_evidence(self):
        self.assertEqual(route_after_repro({"next_step": "unexpected"}), "load_evidence")


class ReproductionRoutingTests(unittest.TestCase):
    def test_reproduced_result_loads_source_evidence(self):
        result = assess_repro(
            {"repro_result": {"classification": "reproduced"}, "repro_attempts": 1}
        )
        self.assertEqual(result["status"], "reproduced")
        self.assertEqual(result["next_step"], "load_evidence")

    def test_broken_or_passing_test_gets_one_repair(self):
        for classification in ("repro_broken", "not_reproduced"):
            retry = assess_repro(
                {"repro_result": {"classification": classification}, "repro_attempts": 1}
            )
            exhausted = assess_repro(
                {"repro_result": {"classification": classification}, "repro_attempts": 2}
            )
            self.assertEqual(retry["next_step"], "repair_repro")
            self.assertEqual(exhausted["next_step"], "load_evidence")
            self.assertEqual(exhausted["status"], classification)

    def test_infrastructure_error_retries_once(self):
        retry = assess_repro(
            {
                "repro_result": {"classification": "infra_error"},
                "repro_attempts": 1,
                "infra_retries": 0,
            }
        )
        exhausted = assess_repro(
            {
                "repro_result": {"classification": "infra_error"},
                "repro_attempts": 2,
                "infra_retries": 1,
            }
        )
        self.assertEqual(retry["next_step"], "run_repro")
        self.assertEqual(exhausted["status"], "could_not_run")


if __name__ == "__main__":
    unittest.main()
