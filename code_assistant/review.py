"""Etap 1 pipeline'u: recenzja pojedynczego pliku z walidacją Pydantic i ponawianiem."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .llm.client import LLMClient, TokenUsage
from .prompts import reviewer_system_prompt
from .schema import Review, review_json_schema

log = logging.getLogger(__name__)

EXT_LANG = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java",
    ".cs": "csharp", ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c",
    ".rb": "ruby", ".php": "php", ".kt": "kotlin", ".sql": "sql",
}


class ReviewFailed(RuntimeError):
    def __init__(self, message: str, attempts: list["Attempt"]):
        super().__init__(message)
        self.attempts = attempts


@dataclass
class Attempt:
    raw: str
    error: str | None


@dataclass
class ReviewResult:
    review: Review
    attempts: list[Attempt]
    usage: TokenUsage = field(default_factory=TokenUsage)


def number_lines(code: str) -> str:
    lines = code.splitlines()
    width = len(str(len(lines))) if lines else 1
    return "\n".join(f"{i:>{width}} | {line}" for i, line in enumerate(lines, 1))


def build_user_message(path: str, code: str) -> str:
    lang = EXT_LANG.get(Path(path).suffix.lower(), "unknown")
    return (
        f"File: {path}\nLanguage: {lang}\nLines: {len(code.splitlines())}\n\n"
        f"```\n{number_lines(code)}\n```"
    )


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def extract_json(text: str) -> str:
    """Wyciąga obiekt JSON z odpowiedzi (toleruje płotki markdown i tekst dookoła)."""
    text = _FENCE.sub("", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("Odpowiedź nie zawiera obiektu JSON.")
    return text[start : end + 1]


def parse_review(raw: str, *, source: str, path: str) -> Review:
    data = json.loads(extract_json(raw))
    if isinstance(data, dict):
        data["file"] = path  # ścieżka jest znana - nie polegamy na modelu
    return Review.model_validate(data, context={"source": source})


def _format_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "\n".join(
            f"- {'.'.join(str(p) for p in e['loc']) or '<root>'}: {e['msg']}" for e in exc.errors()
        )
    return f"- {type(exc).__name__}: {exc}"


def review_file(
    client: LLMClient,
    path: str | Path,
    *,
    code: str | None = None,
    language: str = "pl",
    max_attempts: int | None = None,
) -> ReviewResult:
    path = Path(path)
    code = path.read_text(encoding="utf-8") if code is None else code
    display_path = path.as_posix()
    max_attempts = max_attempts or client.settings.max_attempts

    messages = [
        {"role": "system", "content": reviewer_system_prompt(language)},
        {"role": "user", "content": build_user_message(display_path, code)},
    ]
    attempts: list[Attempt] = []
    usage = TokenUsage()

    for n in range(1, max_attempts + 1):
        resp = client.chat(messages, json_schema=review_json_schema(), label=f"review#{n}")
        usage.add(resp.usage)
        try:
            review = parse_review(resp.content, source=code, path=display_path)
        except (ValueError, ValidationError) as exc:  # json.JSONDecodeError dziedziczy po ValueError
            err = _format_error(exc)
            if resp.finish_reason == "length":
                err += "\n- Odpowiedź została ucięta (limit tokenów). Bądź zwięźlejszy."
            log.warning("Próba %d/%d nieudana:\n%s", n, max_attempts, err)
            attempts.append(Attempt(raw=resp.content, error=err))
            messages += [
                {"role": "assistant", "content": resp.content},
                {
                    "role": "user",
                    "content": "Your previous response failed validation:\n"
                    f"{err}\n\nReturn the corrected, complete JSON object only.",
                },
            ]
            continue
        attempts.append(Attempt(raw=resp.content, error=None))
        return ReviewResult(review=review, attempts=attempts, usage=usage)

    raise ReviewFailed(f"Nie udało się uzyskać poprawnej recenzji po {max_attempts} próbach.", attempts)
