import re
from pathlib import Path

from agent.state import AgentState
from agent.tools import repo


MAX_FILES = 5
MAX_FILE_CHARS = 7_000
MAX_TOTAL_CHARS = 18_000
STOP_WORDS = {
    "after", "before", "from", "into", "item", "page", "should", "that",
    "their", "there", "this", "when", "with", "wrong",
}


def _compact(content: str) -> str:
    if len(content) <= MAX_FILE_CHARS:
        return content
    half = MAX_FILE_CHARS // 2
    return content[:half] + "\n... file excerpt shortened ...\n" + content[-half:]


def _focused_content(repo_path: Path, path: str, terms: list[str]) -> str:
    lines: dict[int, str] = {}

    def add_output(output: str) -> None:
        for source_line in output.splitlines():
            match = re.match(rf"{re.escape(path)}:(\d+):", source_line)
            if match:
                lines[int(match.group(1))] = source_line

    try:
        add_output(repo.read_file(repo_path, path, 1, 60))
    except (FileNotFoundError, ValueError):
        return ""

    for term in terms[:5]:
        search_output = repo.search_code(repo_path, re.escape(term))
        for result_line in search_output.splitlines():
            match = re.match(rf"{re.escape(path)}:(\d+):", result_line)
            if not match:
                continue
            line_number = int(match.group(1))
            try:
                add_output(
                    repo.read_file(
                        repo_path,
                        path,
                        max(1, line_number - 12),
                        line_number + 18,
                    )
                )
            except (FileNotFoundError, ValueError):
                continue

    return _compact("\n".join(lines[number] for number in sorted(lines)))


def _search_candidates(repo_path: Path, terms: list[str]) -> list[str]:
    candidates = []
    for term in terms[:3]:
        output = repo.search_code(repo_path, re.escape(term))
        for line in output.splitlines():
            match = re.match(r"([^:]+):\d+:", line)
            if match and match.group(1) not in candidates:
                candidates.append(match.group(1))
            if len(candidates) >= MAX_FILES:
                return candidates
    return candidates


def _bug_terms(report: str) -> list[str]:
    terms = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]+", report.lower()):
        if len(word) < 4 or word in STOP_WORDS:
            continue
        if word.endswith("ing") and len(word) > 6:
            word = word[:-3]
        elif word.endswith("ed") and len(word) > 5:
            word = word[:-2]
        if word not in terms:
            terms.append(word)
    return terms[:8]


def load_evidence(state: AgentState) -> dict:
    round_number = state.get("evidence_rounds", 0) + 1
    print(f"[load_evidence] loading focused files, round {round_number}")
    repo_path = Path(state["repo_path"])
    existing = dict(state.get("file_evidence", {}))
    requested = state.get("requested_files", [])
    planned = state.get("plan", {}).get("relevant_files", [])
    search_terms = list(
        dict.fromkeys(
            state.get("plan", {}).get("search_terms", [])
            + _bug_terms(state.get("bug_report", ""))
        )
    )
    candidates = requested if requested else planned

    total_chars = sum(len(content) for content in existing.values())
    for path in dict.fromkeys(candidates):
        if path in existing or len(existing) >= MAX_FILES or total_chars >= MAX_TOTAL_CHARS:
            continue
        content = _focused_content(repo_path, path, search_terms)
        if not content:
            continue
        remaining = MAX_TOTAL_CHARS - total_chars
        existing[path] = content[:remaining]
        total_chars += len(existing[path])

    if round_number == 1 and not existing:
        for path in _search_candidates(
            repo_path, state.get("plan", {}).get("search_terms", [])
        ):
            if len(existing) >= MAX_FILES or total_chars >= MAX_TOTAL_CHARS:
                break
            content = _focused_content(repo_path, path, search_terms)
            if not content:
                continue
            remaining = MAX_TOTAL_CHARS - total_chars
            existing[path] = content[:remaining]
            total_chars += len(existing[path])

    print(f"[load_evidence] loaded {len(existing)} files")
    return {
        "file_evidence": existing,
        "evidence_rounds": round_number,
        "requested_files": [],
    }
