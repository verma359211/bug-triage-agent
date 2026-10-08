import json

from pydantic import BaseModel, Field

from agent.llm import invoke_structured
from agent.state import AgentState


class FailureMatch(BaseModel):
    matches_hypothesis: bool = Field(
        description="Whether the Jest assertion failure is the failure predicted by the hypothesis"
    )
    explanation: str


def interpret_result(state: AgentState) -> dict:
    result = state.get("repro_result", {})
    classification = result.get("classification", "infra_error")
    rounds = state.get("investigate_rounds", 0)
    attempts = state.get("repro_attempts", 0)
    print(f"[interpret_result] classification={classification}")

    if classification == "reproduced":
        assessment = invoke_structured(
            FailureMatch,
            "Compare the hypothesis with the Jest failure. Mark it as matching only when the failed "
            "assertion demonstrates the behavior predicted by the hypothesis, rather than an unrelated "
            "test setup or runtime failure.\n\n"
            f"Hypothesis: {json.dumps(state.get('hypothesis', {}))}\n"
            f"Failure: {result.get('failure_message', '')}\n"
            f"Summary: {json.dumps(result.get('summary', {}))}",
        )
        if assessment.matches_hypothesis:
            print("[interpret_result] failure matches hypothesis")
            return {"status": "reproduced", "next_step": "report", "missing_info": ""}
        mismatches = state.get("hypothesis_mismatches", 0) + 1
        if rounds < 3:
            print("[interpret_result] unrelated failure; returning to investigation")
            return {
                "status": "running",
                "next_step": "investigate",
                "confidence": "low",
                "missing_info": assessment.explanation,
                "hypothesis_mismatches": mismatches,
            }
        return {
            "status": "not_reproduced",
            "next_step": "report",
            "hypothesis_mismatches": mismatches,
        }

    if classification == "not_reproduced":
        count = state.get("not_reproduced_count", 0) + 1
        if count <= 2 and rounds < 3:
            print("[interpret_result] test passed; returning to investigation")
            return {
                "status": "running",
                "next_step": "investigate",
                "confidence": "low",
                "missing_info": "The reproduction test passed; inspect why the hypothesis did not produce the reported behavior.",
                "not_reproduced_count": count,
            }
        return {
            "status": "not_reproduced",
            "next_step": "report",
            "not_reproduced_count": count,
        }

    if classification == "repro_broken":
        if attempts < 3:
            print("[interpret_result] generated test is invalid; rewriting")
            return {"status": "running", "next_step": "write_repro"}
        return {"status": "repro_broken", "next_step": "report"}

    retries = state.get("infra_retries", 0)
    if retries < 1:
        print("[interpret_result] infrastructure failed; retrying once")
        return {
            "status": "running",
            "next_step": "run_repro",
            "infra_retries": retries + 1,
        }
    return {"status": "could_not_run", "next_step": "report", "infra_retries": retries}
