import os

from agent.llm import load_dotenv
from agent.state import AgentState
from agent.tools.sandbox import run_repro as run_in_sandbox


def run_repro(state: AgentState) -> dict:
    attempt = state.get("repro_attempts", 0) + 1
    print(f"[run_repro] GitHub Actions attempt {attempt}")
    load_dotenv()
    result = run_in_sandbox(
        state["repro_test"],
        state["commit_sha"],
        repo_url=state["repo_url"],
        token=os.environ["GITHUB_TOKEN"],
    )
    print(f"[run_repro] classification={result['classification']}")
    return {"repro_result": result, "repro_attempts": attempt}

