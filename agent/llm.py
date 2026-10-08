import json
import os
from pathlib import Path
from typing import TypeVar

from langchain_groq import ChatGroq
from pydantic import BaseModel


StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


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


def get_chat_model(
    *, max_tokens: int = 1_000, reasoning_effort: str = "low"
) -> ChatGroq:
    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider != "groq":
        raise ValueError(f"unsupported LLM provider: {provider}")
    model = os.environ.get("LLM_MODEL")
    if not model:
        raise ValueError("LLM_MODEL is required")
    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is required")
    return ChatGroq(
        model=model,
        temperature=0,
        max_tokens=max_tokens,
        max_retries=5,
        reasoning_effort=reasoning_effort,
    )


def invoke_structured(
    schema: type[StructuredModel],
    prompt: str,
    *,
    max_tokens: int = 1_000,
    reasoning_effort: str = "low",
) -> StructuredModel:
    model = get_chat_model(
        max_tokens=max_tokens, reasoning_effort=reasoning_effort
    )
    try:
        return model.with_structured_output(schema, method="json_schema").invoke(prompt)
    except Exception as error:
        if getattr(error, "status_code", None) != 400:
            raise
    json_prompt = (
        prompt
        + "\nReturn only valid JSON matching this schema: "
        + json.dumps(schema.model_json_schema())
    )
    return model.with_structured_output(schema, method="json_mode").invoke(json_prompt)
