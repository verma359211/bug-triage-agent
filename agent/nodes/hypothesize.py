import json

from pydantic import BaseModel, Field

from agent.llm import invoke_structured
from agent.state import AgentState


class Hypothesis(BaseModel):
    file: str = Field(description="One repository-relative file most likely responsible")
    cause: str = Field(description="Concrete faulty behavior in that file")
    reasoning: str = Field(description="Short explanation connecting evidence to the report")


def hypothesize(state: AgentState) -> dict:
    print("[hypothesize] selecting the most likely root cause")
    evidence = state.get("evidence", [])[-8:]
    hypothesis = invoke_structured(
        Hypothesis,
        "Form one bug hypothesis using only the supplied repository evidence. Choose the exact "
        "repository-relative implementation file, not a test or documentation file. Do not propose "
        "a fix.\n\n"
        f"Bug report: {state['bug_report']}\n"
        f"Evidence: {json.dumps(evidence)}",
    )
    print(f"[hypothesize] file={hypothesis.file}")
    return {"hypothesis": hypothesis.model_dump()}
