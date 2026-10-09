from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    bug_report: str
    repo_url: str
    repo_path: str
    commit_sha: str
    layer_guess: str
    parsed_report: dict[str, Any]
    context_document: str
    plan: dict[str, Any]
    file_evidence: dict[str, str]
    diagnosis_evidence: list[dict[str, Any]]
    requested_files: list[str]
    evidence_rounds: int
    hypothesis: dict[str, str]
    confidence: str
    repro_test: str
    repro_attempts: int
    repro_result: dict[str, Any]
    infra_retries: int
    next_step: str
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
        "context_document": "",
        "plan": {},
        "file_evidence": {},
        "diagnosis_evidence": [],
        "requested_files": [],
        "evidence_rounds": 0,
        "hypothesis": {},
        "confidence": "low",
        "repro_test": "",
        "repro_attempts": 0,
        "repro_result": {},
        "infra_retries": 0,
        "next_step": "",
        "status": "running",
        "report": {},
    }
