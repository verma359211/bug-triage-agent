import json
from typing import Literal

from pydantic import BaseModel, Field

from agent.llm import get_chat_model
from agent.state import AgentState


class ConfidenceAssessment(BaseModel):
    confidence: Literal["high", "low"]
    missing_info: str = Field(
        description="Specific additional evidence needed, or an empty string when confidence is high"
    )


def assess_confidence(state: AgentState) -> dict[str, str]:
    print("[assess_confidence] reflecting on evidence quality")
    model = get_chat_model().with_structured_output(
        ConfidenceAssessment, method="json_schema"
    )
    assessment = model.invoke(
        "Assess whether the hypothesis is directly supported by inspected implementation evidence. "
        "High means the named file and faulty behavior are visible in evidence and explain the report. "
        "Low means more repository inspection is required.\n\n"
        f"Bug report: {state['bug_report']}\n"
        f"Hypothesis: {json.dumps(state.get('hypothesis', {}))}\n"
        f"Evidence: {json.dumps(state.get('evidence', [])[-8:])}"
    )
    print(f"[assess_confidence] confidence={assessment.confidence}")
    return {
        "confidence": assessment.confidence,
        "missing_info": assessment.missing_info,
    }
