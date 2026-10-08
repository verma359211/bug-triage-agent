import unittest

from agent.tools.repo import truncate_output


class RepoToolTests(unittest.TestCase):
    def test_truncates_by_line_count(self):
        output = truncate_output("\n".join(str(number) for number in range(250)))
        self.assertIn("output truncated", output)
        self.assertLessEqual(len(output.splitlines()), 201)

    def test_truncates_by_character_count(self):
        output = truncate_output("x" * 9_000)
        self.assertIn("output truncated", output)
        self.assertLess(len(output), 8_100)

    def test_short_output_is_unchanged(self):
        self.assertEqual(truncate_output("one\ntwo"), "one\ntwo")


if __name__ == "__main__":
    unittest.main()

