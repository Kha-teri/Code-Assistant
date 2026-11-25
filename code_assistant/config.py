"""Konfiguracja aplikacji wczytywana z pliku .env / zmiennych środowiskowych."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

ResponseFormatMode = Literal["none", "json_object", "json_schema"]


def _env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str = DEFAULT_MODEL
    temperature: float = 0.2
    max_tokens: int = 8000
    timeout: float = 180.0
    response_format: ResponseFormatMode = "none"
    reasoning_effort: str | None = None
    max_attempts: int = 3
    base_url: str = OPENROUTER_BASE_URL

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "Settings":
        load_dotenv(env_file or PROJECT_ROOT / ".env")
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Brak OPENROUTER_API_KEY. Skopiuj .env.example do .env i uzupełnij klucz."
            )
        mode = _env("CA_RESPONSE_FORMAT", "none")
        if mode not in ("none", "json_object", "json_schema"):
            raise ValueError(f"Nieznany CA_RESPONSE_FORMAT: {mode!r}")
        return cls(
            api_key=api_key,
            model=_env("CA_MODEL", DEFAULT_MODEL),
            temperature=float(_env("CA_TEMPERATURE", "0.2")),
            max_tokens=int(_env("CA_MAX_TOKENS", "8000")),
            timeout=float(_env("CA_TIMEOUT", "180")),
            response_format=mode,  # type: ignore[arg-type]
            reasoning_effort=os.getenv("CA_REASONING_EFFORT", "").strip() or None,
            max_attempts=int(_env("CA_MAX_ATTEMPTS", "3")),
        )
