import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from agent.llm import get_chat_model
from agent.state import AgentState
from agent.tools import repo


MAX_TOOL_CALLS = 6


def failed_generation_text(error: Exception) -> str:
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return ""
    return str(body.get("error", {}).get("failed_generation", ""))


def _tools(repo_path: Path):
    @tool
    def search_code(pattern: str) -> str:
        """Search repository text with a case-insensitive regular expression."""
        return repo.search_code(repo_path, pattern)

    @tool
    def read_file(path: str, line_start: int | None = None, line_end: int | None = None) -> str:
        """Read a repository file, optionally restricted to an inclusive line range."""
        return repo.read_file(repo_path, path, line_start, line_end)

    @tool
    def git_log(path: str) -> str:
        """Show recent commits that changed one repository file."""
        return repo.git_log(repo_path, path)

    @tool
    def git_blame(path: str, line_start: int, line_end: int) -> str:
        """Show commit attribution for an inclusive line range in one file."""
        return repo.git_blame(repo_path, path, line_start, line_end)

    return [search_code, read_file, git_log, git_blame]


def investigate(state: AgentState) -> dict:
    round_number = state.get("investigate_rounds", 0) + 1
    print(f"[investigate] round {round_number}, up to {MAX_TOOL_CALLS} tool calls")
    tools = _tools(Path(state["repo_path"]))
    tools_by_name = {item.name: item for item in tools}
    model = get_chat_model().bind_tools(tools)
    previous_evidence = state.get("evidence", [])
    messages = [
        SystemMessage(
            content=(
                "You investigate software defects. Use the repository tools before drawing a "
                "conclusion. Inspect business rules, relevant implementation files, and Git history "
                "when useful. Focus on identifying one exact file and concrete faulty behavior. "
                "Do not propose a fix. Keep tool queries narrow."
            )
        ),
        HumanMessage(
            content=(
                f"Bug report: {state['bug_report']}\n"
                f"Parsed report: {json.dumps(state.get('parsed_report', {}))}\n"
                f"Missing information from reflection: {state.get('missing_info', '')}\n"
                f"Prior evidence summaries: {json.dumps(previous_evidence[-4:])}\n"
                "Investigate now."
            )
        ),
    ]
    new_evidence: list[dict] = []
    tool_calls_used = 0

    while tool_calls_used < MAX_TOOL_CALLS:
        try:
            response = model.invoke(messages)
        except Exception as error:
            failed_generation = failed_generation_text(error)
            if not failed_generation:
                raise
            print("[investigate] recovered plain-text model conclusion")
            new_evidence.append(
                {
                    "tool": "investigator_notes",
                    "arguments": {},
                    "output": failed_generation,
                }
            )
            break
        messages.append(response)
        if not response.tool_calls:
            if response.content:
                new_evidence.append(
                    {"tool": "investigator_notes", "arguments": {}, "output": str(response.content)}
                )
            break

        for call in response.tool_calls:
            if tool_calls_used >= MAX_TOOL_CALLS:
                break
            tool_calls_used += 1
            selected = tools_by_name.get(call["name"])
            if selected is None:
                output = f"unknown tool: {call['name']}"
            else:
                try:
                    output = str(selected.invoke(call["args"]))
                except Exception as error:
                    output = f"tool error: {type(error).__name__}: {error}"
            print(f"[investigate] {call['name']} {call['args']}")
            new_evidence.append(
                {"tool": call["name"], "arguments": call["args"], "output": output}
            )
            messages.append(ToolMessage(content=output, tool_call_id=call["id"]))

    print(f"[investigate] used {tool_calls_used} tool calls")
    return {
        "evidence": previous_evidence + new_evidence,
        "investigate_rounds": round_number,
    }
