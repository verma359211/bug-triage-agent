import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from agent.llm import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
FRONTEND_DIST = ROOT / "frontend" / "dist"
GITHUB_REPO_PATTERN = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$"
)
MAX_ACTIVE_RUNS = 1
RUN_TTL_SECONDS = 3_600
DEFAULT_RATE_LIMIT = 3
DEFAULT_RATE_WINDOW_SECONDS = 3_600
REQUIRED_SETTINGS = ("GITHUB_TOKEN", "GROQ_API_KEY", "TARGET_REPO")


def canonical_repo(value: str) -> str:
    return value.strip().lower().removesuffix("/").removesuffix(".git")


def allowed_repositories() -> set[str]:
    configured = os.environ.get("ALLOWED_REPOS") or os.environ.get("TARGET_REPO", "")
    return {canonical_repo(value) for value in configured.split(",") if value.strip()}


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        current = time.time() if now is None else now
        cutoff = current - self.window_seconds
        with self._lock:
            recent = [value for value in self._attempts.get(key, []) if value > cutoff]
            if len(recent) >= self.limit:
                self._attempts[key] = recent
                return False
            recent.append(current)
            self._attempts[key] = recent
            return True


rate_limiter = RateLimiter(
    int(os.environ.get("RATE_LIMIT_REQUESTS", DEFAULT_RATE_LIMIT)),
    int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", DEFAULT_RATE_WINDOW_SECONDS)),
)


class RunRequest(BaseModel):
    repo_url: str = Field(min_length=20, max_length=300)
    bug_report: str = Field(min_length=20, max_length=4_000)

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, value: str) -> str:
        value = value.strip()
        if not GITHUB_REPO_PATTERN.fullmatch(value):
            raise ValueError("use a public https://github.com/OWNER/REPOSITORY URL")
        return value

    @field_validator("bug_report")
    @classmethod
    def clean_bug_report(cls, value: str) -> str:
        return value.strip()


@dataclass
class RunRecord:
    id: str
    repo_url: str
    bug_report: str
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    logs: list[str] = field(default_factory=list)
    report: dict | None = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def public(self) -> dict:
        return {
            "id": self.id,
            "repo_url": self.repo_url,
            "bug_report": self.bug_report,
            "status": self.status,
            "logs": list(self.logs),
            "report": self.report,
            "error": self.error,
        }


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, RunRecord] = {}
        self._lock = threading.Lock()

    def create(self, request: RunRequest) -> RunRecord:
        with self._lock:
            self._remove_expired()
            active = sum(
                run.status in {"queued", "running"} for run in self._runs.values()
            )
            if active >= MAX_ACTIVE_RUNS:
                raise RuntimeError("the agent is already handling the maximum number of runs")
            record = RunRecord(
                id=uuid.uuid4().hex[:12],
                repo_url=request.repo_url,
                bug_report=request.bug_report,
            )
            self._runs[record.id] = record
            return record

    def get(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)

    def update(self, run_id: str, **changes) -> None:
        with self._lock:
            record = self._runs[run_id]
            for name, value in changes.items():
                setattr(record, name, value)
            record.updated_at = time.time()

    def append_log(self, run_id: str, message: str) -> None:
        clean = message.strip()
        if not clean:
            return
        with self._lock:
            record = self._runs[run_id]
            record.logs.append(clean[:1_000])
            record.logs = record.logs[-200:]
            record.updated_at = time.time()

    def _remove_expired(self) -> None:
        cutoff = time.time() - RUN_TTL_SECONDS
        expired = [
            run_id
            for run_id, record in self._runs.items()
            if record.updated_at < cutoff
            and record.status in {"completed", "failed"}
        ]
        for run_id in expired:
            del self._runs[run_id]


store = RunStore()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global rate_limiter
    load_dotenv(ROOT / ".env")
    rate_limiter = RateLimiter(
        int(os.environ.get("RATE_LIMIT_REQUESTS", DEFAULT_RATE_LIMIT)),
        int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", DEFAULT_RATE_WINDOW_SECONDS)),
    )
    yield


app = FastAPI(title="Bug Triage Agent", version="0.1.0", lifespan=lifespan)


def _run_agent(record: RunRecord) -> None:
    output_path = RUNS_DIR / f"web-{record.id}.json"
    command = [
        sys.executable,
        "-u",
        "-m",
        "agent.cli",
        "--repo",
        record.repo_url,
        "--report",
        record.bug_report,
        "--output",
        str(output_path),
        "--quiet",
    ]
    store.update(record.id, status="running")
    store.append_log(record.id, "[start] Triage run accepted")
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=os.environ.copy(),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        assert process.stdout is not None
        for line in process.stdout:
            store.append_log(record.id, line)
        exit_code = process.wait()
        if exit_code != 0:
            raise RuntimeError(f"agent process exited with code {exit_code}")
        report = json.loads(output_path.read_text(encoding="utf-8"))
        store.append_log(record.id, "[complete] Report is ready")
        store.update(record.id, status="completed", report=report)
    except Exception as error:
        store.append_log(record.id, f"[error] {error}")
        store.update(record.id, status="failed", error=str(error))


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/ready")
def ready():
    missing = [name for name in REQUIRED_SETTINGS if not os.environ.get(name)]
    payload = {"ready": not missing, "missing": missing}
    return JSONResponse(payload, status_code=200 if not missing else 503)


@app.get("/api/config")
def config() -> dict:
    load_dotenv(ROOT / ".env")
    repositories = allowed_repositories()
    return {
        "default_repo": os.environ.get("TARGET_REPO", ""),
        "model": os.environ.get("LLM_MODEL", "Groq model"),
        "repository_locked": bool(repositories),
    }


@app.post("/api/runs", status_code=202)
def create_run(payload: RunRequest, request: Request) -> dict:
    repositories = allowed_repositories()
    if not repositories:
        raise HTTPException(status_code=503, detail="repository allowlist is not configured")
    if canonical_repo(payload.repo_url) not in repositories:
        raise HTTPException(status_code=403, detail="this showcase only accepts its target repository")
    client = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client):
        raise HTTPException(status_code=429, detail="demo limit reached; try again later")
    try:
        record = store.create(payload)
    except RuntimeError as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    threading.Thread(target=_run_agent, args=(record,), daemon=True).start()
    return {"id": record.id, "status": record.status}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    record = store.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="run not found")
    return record.public()


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        candidate = (FRONTEND_DIST / path).resolve()
        if path and candidate.is_relative_to(FRONTEND_DIST.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
