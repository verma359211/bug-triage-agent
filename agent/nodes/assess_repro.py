from agent.state import AgentState


def assess_repro(state: AgentState) -> dict:
    classification = state.get("repro_result", {}).get("classification", "infra_error")
    attempts = state.get("repro_attempts", 0)
    print(f"[assess_repro] classification={classification}")

    if classification == "reproduced":
        return {"status": "reproduced", "next_step": "load_evidence"}
    if classification in {"repro_broken", "not_reproduced"} and attempts < 2:
        return {"status": "running", "next_step": "repair_repro"}
    if classification == "infra_error" and state.get("infra_retries", 0) < 1:
        return {
            "status": "running",
            "next_step": "run_repro",
            "infra_retries": state.get("infra_retries", 0) + 1,
        }

    status = "could_not_run" if classification == "infra_error" else classification
    return {"status": status, "next_step": "load_evidence"}
