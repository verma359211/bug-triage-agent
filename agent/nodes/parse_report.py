from typing import Literal

from pydantic import BaseModel, Field

from agent.llm import invoke_structured
from agent.state import AgentState


class ParsedReport(BaseModel):
    layer: Literal["backend", "frontend", "unknown"]
    symptom: str = Field(description="Concise description of the observed wrong behavior")
    expected_behavior: str = Field(description="Concise description of the expected behavior")
    search_terms: list[str] = Field(description="Three to six code-search terms")


def parse_report(state: AgentState) -> dict:
    print("[parse_report] extracting symptom and likely layer")
    parsed = invoke_structured(
        ParsedReport,
        "Classify and normalize this software defect report. Do not diagnose the cause yet. "
        "Use backend for pricing, tax, discounts, stock, checkout, orders, services, or API behavior. "
        "Use frontend only for browser rendering, displayed client state, or direct UI interactions.\n\n"
        + state["bug_report"],
    )
    print(f"[parse_report] layer={parsed.layer}")
    return {"layer_guess": parsed.layer, "parsed_report": parsed.model_dump()}
