import unittest

from agent.nodes.load_evidence import _bug_terms


class BugTermTests(unittest.TestCase):
    def test_derives_code_friendly_terms_from_report(self):
        terms = _bug_terms("Removing an item leaves the displayed total stale.")

        self.assertIn("remov", terms)
        self.assertIn("total", terms)
        self.assertNotIn("item", terms)


if __name__ == "__main__":
    unittest.main()
