import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from langchain_core.tools import tool

from agent.llm import get_chat_model


@tool
def lookup_marker(value: str) -> str:
    """Return a marker for the supplied value."""
    return f"marker:{value}"


def main() -> int:
    model = get_chat_model().bind_tools([lookup_marker], tool_choice="required")
    response = model.invoke(
        "Call lookup_marker exactly once with the value 'ready'. Do not answer directly."
    )
    calls = response.tool_calls
    ok = (
        len(calls) == 1
        and calls[0]["name"] == "lookup_marker"
        and calls[0]["args"].get("value") == "ready"
    )
    print(f"tool_calling={'ok' if ok else 'failed'}")
    if calls:
        print(f"tool={calls[0]['name']} value={calls[0]['args'].get('value')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

