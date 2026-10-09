import unittest

from agent.nodes.plan_run import InvestigationPlan, clean_test_source, recover_plan


class ReproductionSourceTests(unittest.TestCase):
    def test_keeps_plain_source(self):
        source = "test('works', () => expect(true).toBe(true));"
        self.assertEqual(clean_test_source(source), source)

    def test_removes_javascript_fence(self):
        self.assertEqual(
            clean_test_source("```javascript\ntest('works', () => {});\n```"),
            "test('works', () => {});",
        )

    def test_empty_source_stays_empty_for_frontend_plan(self):
        self.assertEqual(clean_test_source("   "), "")

    def test_plan_accepts_description_as_symptom_alias(self):
        plan = InvestigationPlan.model_validate(
            {
                "layer": "backend",
                "description": "Quantity zero is rejected.",
                "expected_behavior": "Quantity zero removes the item.",
                "relevant_files": ["src/services/cart.js"],
                "search_terms": ["quantity"],
                "reproduction_test": "test('removes', () => {});",
                "reproduction_reason": "Exercises the contract.",
            }
        )

        self.assertEqual(plan.symptom, "Quantity zero is rejected.")

    def test_recovers_values_wrapped_in_properties(self):
        error = RuntimeError("parse failed")
        error.llm_output = (
            '{"description":"","properties":{"layer":"frontend",'
            '"symptom":"Total stays stale","expected_behavior":"Total updates",'
            '"relevant_files":["frontend/src/CartPage.jsx"],'
            '"search_terms":["remove"],"reproduction_test":"",'
            '"reproduction_reason":"Browser state bug"}}'
        )

        plan = recover_plan(error)

        self.assertEqual(plan.layer, "frontend")


if __name__ == "__main__":
    unittest.main()
