from pathlib import Path

from agent.state import AgentState
from agent.tools.repo import clone_or_pull


def ensure_repo(state: AgentState) -> dict[str, str]:
    print("[ensure_repo] cloning or updating target")
    root = Path(__file__).resolve().parents[2]
    repo_path, commit_sha = clone_or_pull(state["repo_url"], root / ".workdir")
    print(f"[ensure_repo] HEAD {commit_sha[:12]}")
    return {"repo_path": str(repo_path), "commit_sha": commit_sha}

