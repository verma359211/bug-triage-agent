from agent.state import AgentState


def _evidence_lines(state: AgentState) -> list[str]:
    hypothesis_file = state.get("hypothesis", {}).get("file", "")
    preferred: list[str] = []
    fallback: list[str] = []
    for item in state.get("evidence", []):
        if item.get("tool") not in {"search_code", "read_file"}:
            continue
        for line in str(item.get("output", "")).splitlines():
            if line.count(":") < 2 or not line.split(":", 2)[1].isdigit():
                continue
            fallback.append(line)
            if hypothesis_file and line.startswith(f"{hypothesis_file}:"):
                preferred.append(line)
    return (preferred or fallback)[:6]


def report(state: AgentState) -> dict:
    layer = state.get("layer_guess", "unknown")
    existing_status = state.get("status", "running")
    if existing_status not in {"", "running"}:
        status = existing_status
    elif layer == "frontend":
        status = "hypothesis_only_frontend"
    elif state.get("confidence") == "high":
        status = "hypothesis_only"
    else:
        status = "insufficient_evidence"

    hypothesis = state.get("hypothesis", {})
    evidence = _evidence_lines(state)
    report_data = {
        "status": status,
        "file": hypothesis.get("file", ""),
        "cause": hypothesis.get("cause", ""),
        "reasoning": hypothesis.get("reasoning", ""),
        "evidence": evidence,
        "confidence": state.get("confidence", "low"),
        "repro_test": state.get("repro_test", ""),
        "attempts": state.get("repro_attempts", 0),
        "failure_message": state.get("repro_result", {}).get("failure_message", ""),
        "summary": state.get("repro_result", {}).get("summary", {}),
        "total_seconds": 0.0,
    }
    evidence_markdown = "\n".join(f"- `{line}`" for line in evidence) or "- No line evidence captured"
    report_data["markdown"] = (
        f"# Bug triage report\n\n"
        f"- Status: `{status}`\n"
        f"- File: `{report_data['file']}`\n"
        f"- Confidence: `{report_data['confidence']}`\n"
        f"- Reproduction attempts: `{report_data['attempts']}`\n"
        f"- Cause: {report_data['cause']}\n\n"
        f"## Evidence\n\n{evidence_markdown}\n"
    )
    print(f"[report] status={status}")
    return {"status": status, "report": report_data}
