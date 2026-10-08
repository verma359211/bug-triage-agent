import unittest
from unittest.mock import patch

from pydantic import ValidationError

from agent.web import RunRequest, RunStore, health


class RunRequestTests(unittest.TestCase):
    def test_accepts_public_github_url(self):
        request = RunRequest(
            repo_url="https://github.com/example/project.git",
            bug_report="Checkout accepts more units than are available.",
        )

        self.assertEqual(request.repo_url, "https://github.com/example/project.git")

    def test_rejects_non_github_url(self):
        with self.assertRaises(ValidationError):
            RunRequest(
                repo_url="https://example.com/project.git",
                bug_report="Checkout accepts more units than are available.",
            )


class RunStoreTests(unittest.TestCase):
    def test_keeps_only_latest_two_hundred_logs(self):
        run_store = RunStore()
        record = run_store.create(
            RunRequest(
                repo_url="https://github.com/example/project",
                bug_report="Checkout accepts more units than are available.",
            )
        )

        for index in range(205):
            run_store.append_log(record.id, f"line {index}")

        self.assertEqual(len(run_store.get(record.id).logs), 200)
        self.assertEqual(run_store.get(record.id).logs[0], "line 5")

    @patch("agent.web.MAX_ACTIVE_RUNS", 1)
    def test_limits_concurrent_runs(self):
        run_store = RunStore()
        request = RunRequest(
            repo_url="https://github.com/example/project",
            bug_report="Checkout accepts more units than are available.",
        )
        run_store.create(request)

        with self.assertRaises(RuntimeError):
            run_store.create(request)


class WebApiTests(unittest.TestCase):
    def test_health_payload(self):
        self.assertEqual(health(), {"ok": True})


if __name__ == "__main__":
    unittest.main()
