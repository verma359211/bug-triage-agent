import os
from pathlib import Path

from langchain_groq import ChatGroq


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


def get_chat_model() -> ChatGroq:
    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider != "groq":
        raise ValueError(f"unsupported LLM provider: {provider}")
    model = os.environ.get("LLM_MODEL")
    if not model:
        raise ValueError("LLM_MODEL is required")
    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is required")
    return ChatGroq(model=model, temperature=0, max_tokens=1_000, max_retries=5)

