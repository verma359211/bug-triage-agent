import unittest

from eval.run_eval import cause_matches


class CauseMatchTests(unittest.TestCase):
    def test_matches_keywords_across_cause_and_reasoning(self):
        report = {
            "cause": "Tax is rounded for each line.",
            "reasoning": "It should round once on the subtotal.",
        }

        self.assertTrue(cause_matches(report, ["tax", "line", "subtotal", "round"]))

    def test_allows_one_missing_keyword_out_of_four(self):
        report = {
            "cause": "An off-by-one check allows quantity above stock.",
            "reasoning": "",
        }

        self.assertTrue(cause_matches(report, ["stock", "quantity", "one", "boundary"]))

    def test_rejects_weak_cause_match(self):
        report = {"cause": "The price is wrong.", "reasoning": "",}

        self.assertFalse(cause_matches(report, ["combined", "discount", "50", "cap"]))


if __name__ == "__main__":
    unittest.main()
