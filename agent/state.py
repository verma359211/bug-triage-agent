from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    bug_report: str
    repo_url: str
    repo_path: str
    commit_sha: str
    layer_guess: str
    parsed_report: dict[str, Any]
    evidence: list[dict[str, Any]]
    hypothesis: dict[str, str]
    confidence: str
    missing_info: str
    investigate_rounds: int
    repro_test: str
    repro_attempts: int
    repro_result: dict[str, Any]
    status: str
    report: dict[str, Any]


def initial_state(repo_url: str, bug_report: str) -> AgentState:
    return {
        "bug_report": bug_report,
        "repo_url": repo_url,
        "repo_path": "",
        "commit_sha": "",
        "layer_guess": "unknown",
        "parsed_report": {},
        "evidence": [],
        "hypothesis": {},
        "confidence": "low",
        "missing_info": "",
        "investigate_rounds": 0,
        "repro_test": "",
        "repro_attempts": 0,
        "repro_result": {},
        "status": "running",
        "report": {},
    }

