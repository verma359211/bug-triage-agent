import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

from agent.llm import get_chat_model, invoke_structured
from agent.state import AgentState
from agent.tools import repo


class ReproductionTest(BaseModel):
    test_source: str = Field(description="Complete source for one Jest test file")


def _clean_test_source(content: str) -> str:
    source = content.strip()
    if source.startswith("```"):
        lines = source.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        source = "\n".join(lines).strip()
    if not source:
        raise ValueError("model returned an empty reproduction test")
    return source


def _compact_output(output: object) -> str:
    text = str(output)
    if len(text) <= 2_400:
        return text
    return text[:1_200] + "\n... excerpt shortened ...\n" + text[-1_200:]


def _repository_context(state: AgentState) -> list[dict[str, str]]:
    repo_path = Path(state["repo_path"])
    candidates = [
        state.get("hypothesis", {}).get("file", ""),
        "docs/business-rules.md",
        "src/data/store.js",
        "src/app.js",
    ]
    tests_path = repo_path / "tests"
    if tests_path.is_dir():
        candidates.extend(
            path.relative_to(repo_path).as_posix()
            for path in sorted(tests_path.glob("*.test.js"))[:3]
        )

    context = []
    for relative_path in dict.fromkeys(path for path in candidates if path):
        try:
            content = repo.read_file(repo_path, relative_path)
        except (FileNotFoundError, ValueError):
            continue
        context.append({"path": relative_path, "content": _compact_output(content)})
    return context


def write_repro(state: AgentState) -> dict[str, str]:
    attempt = state.get("repro_attempts", 0) + 1
    print(f"[write_repro] preparing Jest test for attempt {attempt}")
    prior_result = state.get("repro_result", {})
    compact_evidence = [
        {
            "tool": item.get("tool"),
            "arguments": item.get("arguments", {}),
            "output": _compact_output(item.get("output", "")),
        }
        for item in state.get("evidence", [])[-6:]
    ]
    api_lines = []
    for item in compact_evidence:
        for line in item["output"].splitlines():
            if "function " in line or "module.exports" in line or "exports." in line:
                api_lines.append(line)
    repository_context = _repository_context(state)
    max_tokens = int(os.environ.get("LLM_REPRO_MAX_TOKENS", "2000"))
    prompt = (
        "Write one minimal Jest test that asserts the CORRECT behavior described by the bug report "
        "and business-rule evidence. The test will be saved as repro/repro.test.js in the target "
        "repository, so imports must use paths such as ../src/app or ../src/services/name. You may "
        "use Supertest or direct service imports. Do not test the implementation's current wrong "
        "behavior. Import only symbols that the inspected files actually export; exercise an internal "
        "helper through its exported public function. Match the exact function parameter order shown "
        "in the inspected declaration; do not wrap positional arguments in an invented options object. "
        "Copy working import and setup patterns from the supplied existing tests. Never invent a "
        "function, export, product field, or route that is absent from the supplied repository context. "
        "Keep the file under 20 lines with exactly one test and one primary expectation. Prefer calling "
        "an exported service function directly when that can demonstrate the rule; avoid verbose HTTP "
        "setup and do not assert unrelated totals. "
        "Return complete JavaScript source with no Markdown fences. Keep the test isolated and "
        "deterministic.\n\n"
        f"Bug report: {state['bug_report']}\n"
        f"Hypothesis: {json.dumps(state.get('hypothesis', {}))}\n"
        f"Evidence: {json.dumps(compact_evidence)}\n"
        f"Observed function and export lines: {json.dumps(api_lines[:20])}\n"
        f"Direct repository context: {json.dumps(repository_context)}\n"
        f"Previous test source: {state.get('repro_test', '')}\n"
        f"Previous result requiring correction: {json.dumps(prior_result)}"
    )
    try:
        source = invoke_structured(
            ReproductionTest,
            prompt,
            max_tokens=max_tokens,
            reasoning_effort="medium",
        )
        source = source.test_source
    except Exception as error:
        if getattr(error, "status_code", None) != 400:
            raise
        print("[write_repro] structured modes failed; requesting plain source")
        response = get_chat_model(
            max_tokens=max_tokens, reasoning_effort="medium"
        ).invoke(
            prompt
            + "\nYou have no tools and must not request any. Output only the JavaScript test "
            "source. Do not use Markdown fences."
        )
        source = str(response.content)
    return {"repro_test": _clean_test_source(source)}
