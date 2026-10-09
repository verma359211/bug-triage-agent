import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from agent.nodes.assess_repro import assess_repro
from agent.nodes.diagnose import diagnose
from agent.nodes.ensure_repo import ensure_repo
from agent.nodes.load_evidence import load_evidence
from agent.nodes.plan_run import plan_run
from agent.nodes.repair_repro import repair_repro
from agent.nodes.report import report
from agent.nodes.run_repro import run_repro
from agent.state import AgentState, initial_state


def route_after_plan(state: AgentState) -> str:
    return "load_evidence" if state.get("layer_guess") == "frontend" else "run_repro"


def route_after_repro(state: AgentState) -> str:
    next_step = state.get("next_step", "load_evidence")
    if next_step not in {"load_evidence", "repair_repro", "run_repro"}:
        return "load_evidence"
    return next_step


def route_after_diagnosis(state: AgentState) -> str:
    if state.get("next_step") == "repair_repro":
        return "repair_repro"
    if state.get("requested_files") and state.get("evidence_rounds", 0) < 2:
        return "load_evidence"
    return "report"


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("ensure_repo", ensure_repo)
    builder.add_node("plan_run", plan_run)
    builder.add_node("run_repro", run_repro)
    builder.add_node("assess_repro", assess_repro)
    builder.add_node("repair_repro", repair_repro)
    builder.add_node("load_evidence", load_evidence)
    builder.add_node("diagnose", diagnose)
    builder.add_node("report", report)

    builder.add_edge(START, "ensure_repo")
    builder.add_edge("ensure_repo", "plan_run")
    builder.add_conditional_edges(
        "plan_run",
        route_after_plan,
        {"run_repro": "run_repro", "load_evidence": "load_evidence"},
    )
    builder.add_edge("run_repro", "assess_repro")
    builder.add_conditional_edges(
        "assess_repro",
        route_after_repro,
        {
            "run_repro": "run_repro",
            "repair_repro": "repair_repro",
            "load_evidence": "load_evidence",
        },
    )
    builder.add_edge("repair_repro", "run_repro")
    builder.add_edge("load_evidence", "diagnose")
    builder.add_conditional_edges(
        "diagnose",
        route_after_diagnosis,
        {
            "load_evidence": "load_evidence",
            "repair_repro": "repair_repro",
            "report": "report",
        },
    )
    builder.add_edge("report", END)
    return builder.compile()


def _save_run(report_data: dict) -> Path:
    runs_dir = Path(__file__).resolve().parents[1] / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    path = runs_dir / f"{timestamp}-{uuid.uuid4().hex[:8]}.json"
    path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    return path


def run_agent(repo_url: str, bug_report: str, *, save: bool = True) -> AgentState:
    started = time.monotonic()
    result: AgentState = build_graph().invoke(
        initial_state(repo_url, bug_report),
        config={"recursion_limit": 25},
    )
    result["report"]["total_seconds"] = round(time.monotonic() - started, 2)
    if save:
        path = _save_run(result["report"])
        print(f"[run] saved {path}")
    return result
