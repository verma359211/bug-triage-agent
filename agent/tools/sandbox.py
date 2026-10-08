import base64
import io
import json
import re
import time
import uuid
import zipfile
from typing import Any
from urllib.parse import quote

import httpx


GITHUB_API = "https://api.github.com"
WORKFLOW_FILE = "repro.yml"
MAX_FAILURE_CHARS = 8_000


def _repo_slug(repo_url: str) -> str:
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", repo_url.rstrip("/"))
    if not match:
        raise ValueError("repo_url must be a GitHub repository URL")
    return f"{match.group(1)}/{match.group(2)}"


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "bug-triage-agent-v0",
    }


def _failure_message(result: dict[str, Any]) -> str:
    for suite in result.get("testResults", []):
        message = suite.get("failureMessage")
        if message:
            return str(message)[:MAX_FAILURE_CHARS]
        for assertion in suite.get("assertionResults", []):
            messages = assertion.get("failureMessages") or []
            if messages:
                return str(messages[0])[:MAX_FAILURE_CHARS]
    return ""


def classify_jest_result(result: dict[str, Any]) -> tuple[str, str, dict[str, int]]:
    keys = (
        "numTotalTestSuites",
        "numPassedTestSuites",
        "numFailedTestSuites",
        "numTotalTests",
        "numPassedTests",
        "numFailedTests",
    )
    summary = {key: int(result.get(key, 0)) for key in keys}

    if summary["numFailedTests"] > 0:
        classification = "reproduced"
    elif summary["numFailedTestSuites"] > 0:
        classification = "repro_broken"
    elif summary["numPassedTests"] > 0:
        classification = "not_reproduced"
    else:
        classification = "infra_error"

    return classification, _failure_message(result), summary


def get_default_branch_sha(repo_url: str, token: str) -> str:
    repo = _repo_slug(repo_url)
    with httpx.Client(headers=_headers(token), follow_redirects=True, timeout=30) as client:
        repository = client.get(f"{GITHUB_API}/repos/{repo}")
        repository.raise_for_status()
        default_branch = repository.json()["default_branch"]
        ref = client.get(
            f"{GITHUB_API}/repos/{repo}/git/ref/heads/{quote(default_branch, safe='')}"
        )
        ref.raise_for_status()
        return ref.json()["object"]["sha"]


def run_repro(
    test_source: str,
    commit_sha: str,
    *,
    repo_url: str,
    token: str,
    poll_seconds: float = 5,
    timeout_seconds: float = 300,
) -> dict[str, Any]:
    started = time.monotonic()
    unique_id = uuid.uuid4().hex[:12]
    branch = f"repro/{unique_id}"
    display_title = f"repro-{unique_id}"
    repo = _repo_slug(repo_url)
    run_id: int | None = None
    artifact_id: int | None = None
    branch_created = False
    dispatch_sent = False
    classification = "infra_error"
    failure_message = ""
    summary: dict[str, Any] = {}
    cleanup_errors: list[str] = []

    with httpx.Client(headers=_headers(token), follow_redirects=True, timeout=30) as client:
        try:
            create_ref = client.post(
                f"{GITHUB_API}/repos/{repo}/git/refs",
                json={"ref": f"refs/heads/{branch}", "sha": commit_sha},
            )
            create_ref.raise_for_status()
            branch_created = True

            encoded_source = base64.b64encode(test_source.encode("utf-8")).decode("ascii")
            commit_test = client.put(
                f"{GITHUB_API}/repos/{repo}/contents/repro/repro.test.js",
                json={
                    "message": "Add reproduction test",
                    "content": encoded_source,
                    "branch": branch,
                },
            )
            commit_test.raise_for_status()

            dispatch = client.post(
                f"{GITHUB_API}/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/dispatches",
                json={"ref": branch, "inputs": {"run_id": unique_id}},
            )
            dispatch.raise_for_status()
            dispatch_sent = True

            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                runs_response = client.get(
                    f"{GITHUB_API}/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs",
                    params={"branch": branch, "event": "workflow_dispatch", "per_page": 20},
                )
                runs_response.raise_for_status()
                matching_run = next(
                    (
                        run
                        for run in runs_response.json().get("workflow_runs", [])
                        if run.get("display_title") == display_title
                    ),
                    None,
                )
                if matching_run:
                    run_id = int(matching_run["id"])
                    if matching_run.get("status") == "completed":
                        break
                time.sleep(poll_seconds)
            else:
                raise TimeoutError("GitHub Actions reproduction timed out")

            artifacts_response = client.get(
                f"{GITHUB_API}/repos/{repo}/actions/runs/{run_id}/artifacts"
            )
            artifacts_response.raise_for_status()
            artifact = next(
                (
                    item
                    for item in artifacts_response.json().get("artifacts", [])
                    if item.get("name") == "result" and not item.get("expired")
                ),
                None,
            )
            if not artifact:
                raise RuntimeError("result artifact was not uploaded")
            artifact_id = int(artifact["id"])

            archive_response = client.get(artifact["archive_download_url"])
            archive_response.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
                with archive.open("result.json") as result_file:
                    jest_result = json.load(result_file)

            classification, failure_message, summary = classify_jest_result(jest_result)
        except Exception as error:
            classification = "infra_error"
            failure_message = str(error)[:MAX_FAILURE_CHARS]
            summary = {"error_type": type(error).__name__}
        finally:
            if dispatch_sent and run_id is None:
                try:
                    runs_response = client.get(
                        f"{GITHUB_API}/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs",
                        params={
                            "branch": branch,
                            "event": "workflow_dispatch",
                            "per_page": 20,
                        },
                    )
                    runs_response.raise_for_status()
                    matching_run = next(
                        (
                            run
                            for run in runs_response.json().get("workflow_runs", [])
                            if run.get("display_title") == display_title
                        ),
                        None,
                    )
                    if matching_run:
                        run_id = int(matching_run["id"])
                except Exception as error:
                    cleanup_errors.append(f"locate workflow run: {error}")
            if branch_created:
                try:
                    delete_ref = client.delete(
                        f"{GITHUB_API}/repos/{repo}/git/refs/heads/{branch}"
                    )
                    delete_ref.raise_for_status()
                except Exception as error:
                    cleanup_errors.append(f"branch: {error}")
            if artifact_id is not None:
                try:
                    delete_artifact = client.delete(
                        f"{GITHUB_API}/repos/{repo}/actions/artifacts/{artifact_id}"
                    )
                    delete_artifact.raise_for_status()
                except Exception as error:
                    cleanup_errors.append(f"artifact: {error}")
            if run_id is not None:
                try:
                    delete_run = client.delete(
                        f"{GITHUB_API}/repos/{repo}/actions/runs/{run_id}"
                    )
                    delete_run.raise_for_status()
                except Exception as error:
                    cleanup_errors.append(f"workflow run: {error}")

    if cleanup_errors:
        summary["cleanup_errors"] = cleanup_errors

    return {
        "classification": classification,
        "failure_message": failure_message,
        "summary": summary,
        "seconds": round(time.monotonic() - started, 2),
    }
