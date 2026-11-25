"""Szablony promptów. Treść trzymana w plikach .md, aby łatwo ją wersjonować i porównywać."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..schema import review_json_schema

PROMPTS_DIR = Path(__file__).resolve().parent

LANGUAGES = {"pl": "Polish", "en": "English"}


@lru_cache
def _load(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def reviewer_system_prompt(language: str = "pl") -> str:
    schema = json.dumps(review_json_schema(), ensure_ascii=False, separators=(",", ":"))
    return (
        _load("reviewer_system.md")
        .replace("{language}", LANGUAGES.get(language, language))
        .replace("{schema}", schema)
    )
