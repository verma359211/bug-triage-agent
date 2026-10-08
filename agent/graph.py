import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from agent.nodes.assess_confidence import assess_confidence
from agent.nodes.ensure_repo import ensure_repo
from agent.nodes.hypothesize import hypothesize
from agent.nodes.investigate import investigate
from agent.nodes.interpret_result import interpret_result
from agent.nodes.parse_report import parse_report
from agent.nodes.report import report
from agent.nodes.run_repro import run_repro
from agent.nodes.write_repro import write_repro
from agent.state import AgentState, initial_state


def route_after_confidence(state: AgentState) -> str:
    if state.get("layer_guess") == "frontend":
        return "report"
    if state.get("confidence") == "low" and state.get("investigate_rounds", 0) < 3:
        return "investigate"
    return "write_repro"


def route_after_interpretation(state: AgentState) -> str:
    next_step = state.get("next_step", "report")
    if next_step not in {"report", "investigate", "write_repro", "run_repro"}:
        return "report"
    return next_step


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("ensure_repo", ensure_repo)
    builder.add_node("parse_report", parse_report)
    builder.add_node("investigate", investigate)
    builder.add_node("hypothesize", hypothesize)
    builder.add_node("assess_confidence", assess_confidence)
    builder.add_node("write_repro", write_repro)
    builder.add_node("run_repro", run_repro)
    builder.add_node("interpret_result", interpret_result)
    builder.add_node("report", report)
    builder.add_edge(START, "ensure_repo")
    builder.add_edge("ensure_repo", "parse_report")
    builder.add_edge("parse_report", "investigate")
    builder.add_edge("investigate", "hypothesize")
    builder.add_edge("hypothesize", "assess_confidence")
    builder.add_conditional_edges(
        "assess_confidence",
        route_after_confidence,
        {
            "investigate": "investigate",
            "report": "report",
            "write_repro": "write_repro",
        },
    )
    builder.add_edge("write_repro", "run_repro")
    builder.add_edge("run_repro", "interpret_result")
    builder.add_conditional_edges(
        "interpret_result",
        route_after_interpretation,
        {
            "report": "report",
            "investigate": "investigate",
            "write_repro": "write_repro",
            "run_repro": "run_repro",
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
    graph = build_graph()
    result: AgentState = graph.invoke(
        initial_state(repo_url, bug_report),
        config={"recursion_limit": 40},
    )
    result["report"]["total_seconds"] = round(time.monotonic() - started, 2)
    if save:
        path = _save_run(result["report"])
        print(f"[run] saved {path}")
    return result
