import unittest

from agent.nodes.write_repro import _clean_test_source, _compact_output


class ReproductionSourceTests(unittest.TestCase):
    def test_keeps_plain_source(self):
        source = "test('works', () => expect(true).toBe(true));"
        self.assertEqual(_clean_test_source(source), source)

    def test_removes_javascript_fence(self):
        self.assertEqual(
            _clean_test_source("```javascript\ntest('works', () => {});\n```"),
            "test('works', () => {});",
        )

    def test_rejects_empty_source(self):
        with self.assertRaises(ValueError):
            _clean_test_source("   ")

    def test_compaction_preserves_file_exports_at_end(self):
        output = "start\n" + ("middle\n" * 500) + "module.exports = { calculateTotals };"
        compact = _compact_output(output)
        self.assertIn("start", compact)
        self.assertIn("module.exports = { calculateTotals };", compact)
        self.assertIn("excerpt shortened", compact)


if __name__ == "__main__":
    unittest.main()
