import re
import subprocess
from pathlib import Path


MAX_LINES = 200
MAX_CHARS = 8_000
SKIP_DIRECTORIES = {".git", "node_modules", "coverage", "dist", "build"}


def truncate_output(text: str, max_lines: int = MAX_LINES, max_chars: int = MAX_CHARS) -> str:
    lines = text.splitlines()
    truncated = len(lines) > max_lines
    output = "\n".join(lines[:max_lines])
    if len(output) > max_chars:
        output = output[:max_chars]
        truncated = True
    if truncated:
        output = output.rstrip() + "\n... output truncated ..."
    return output


def _run_git(repo_path: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.stdout.strip()


def _repo_name(repo_url: str) -> str:
    name = repo_url.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".git"):
        name = name[:-4]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise ValueError("repository URL has an invalid name")
    return name


def clone_or_pull(repo_url: str, workdir: Path) -> tuple[Path, str]:
    workdir.mkdir(parents=True, exist_ok=True)
    repo_path = workdir / _repo_name(repo_url)
    if (repo_path / ".git").is_dir():
        _run_git(repo_path, "pull", "--ff-only")
    elif repo_path.exists():
        raise RuntimeError(f"work directory exists but is not a Git repository: {repo_path}")
    else:
        subprocess.run(
            ["git", "clone", repo_url, str(repo_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    return repo_path, _run_git(repo_path, "rev-parse", "HEAD")


def _safe_file(repo_path: Path, relative_path: str) -> Path:
    root = repo_path.resolve()
    candidate = (root / relative_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("path must stay inside the repository")
    if not candidate.is_file():
        raise FileNotFoundError(relative_path)
    return candidate


def search_code(repo_path: Path, pattern: str) -> str:
    try:
        expression = re.compile(pattern, re.IGNORECASE)
    except re.error as error:
        return f"invalid regular expression: {error}"

    matches: list[str] = []
    for path in sorted(repo_path.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        relative = path.relative_to(repo_path).as_posix()
        for line_number, line in enumerate(lines, start=1):
            if expression.search(line):
                matches.append(f"{relative}:{line_number}: {line.strip()}")
                if len(matches) >= MAX_LINES:
                    return truncate_output("\n".join(matches) + "\n... output truncated ...")
    return truncate_output("\n".join(matches) if matches else "no matches")


def read_file(
    repo_path: Path,
    relative_path: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    path = _safe_file(repo_path, relative_path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(1, start_line or 1)
    end = min(len(lines), end_line or len(lines))
    if end < start:
        raise ValueError("end_line must be greater than or equal to start_line")
    relative = path.relative_to(repo_path.resolve()).as_posix()
    output = "\n".join(
        f"{relative}:{line_number}: {lines[line_number - 1]}"
        for line_number in range(start, end + 1)
    )
    return truncate_output(output)


def git_log(repo_path: Path, relative_path: str) -> str:
    _safe_file(repo_path, relative_path)
    output = _run_git(
        repo_path,
        "log",
        "--oneline",
        "--decorate",
        "--max-count=30",
        "--",
        relative_path,
    )
    return truncate_output(output or "no history")


def git_blame(
    repo_path: Path,
    relative_path: str,
    start_line: int,
    end_line: int,
) -> str:
    _safe_file(repo_path, relative_path)
    if start_line < 1 or end_line < start_line:
        raise ValueError("invalid blame line range")
    output = _run_git(
        repo_path,
        "blame",
        "-L",
        f"{start_line},{end_line}",
        "--",
        relative_path,
    )
    return truncate_output(output)

