"""Modele Pydantic opisujące wynik recenzji oraz eksport ich JSON Schema.

Walidacja ma dwa poziomy:
1. struktura (typy, enumy, zakresy) - zawsze;
2. weryfikacja względem źródła - gdy w kontekście walidacji przekazano
   `{"source": <kod>}`: pole `evidence` musi być dosłownym cytatem z kodu,
   a numery linii muszą mieścić się w pliku. To pierwsza linia obrony przed
   halucynacjami i fałszywymi alarmami.
"""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

SCHEMA_VERSION = "1.0"


class Category(str, Enum):
    BUG = "bug"
    READABILITY = "readability"
    PERFORMANCE = "performance"
    TESTING = "testing"
    SECURITY = "security"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def rank(self) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1}[self.value]


_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS.sub(" ", text).strip()


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    id: str = Field(description="Identyfikator uwagi w obrębie recenzji, np. 'F1'.", pattern=r"^F\d+$")
    category: Category
    severity: Severity
    title: str = Field(min_length=3, max_length=160, description="Krótki tytuł problemu.")
    line_start: int = Field(ge=1, description="Pierwsza linia problemu (numeracja od 1).")
    line_end: int = Field(ge=1, description="Ostatnia linia problemu (włącznie).")
    evidence: str = Field(
        min_length=1,
        description="Dosłowny cytat z analizowanego kodu (bez numerów linii), który dowodzi problemu.",
    )
    explanation: str = Field(min_length=10, description="Uzasadnienie: dlaczego to jest problem i jakie ma skutki.")
    suggestion: str = Field(min_length=3, description="Konkretna propozycja poprawki.")
    confidence: float = Field(ge=0.0, le=1.0, description="Pewność recenzenta, że to prawdziwy problem (0-1).")

    @model_validator(mode="after")
    def _check_lines(self) -> "Finding":
        if self.line_end < self.line_start:
            raise ValueError(f"{self.id}: line_end ({self.line_end}) < line_start ({self.line_start})")
        return self

    @field_validator("evidence")
    @classmethod
    def _evidence_in_source(cls, value: str, info: ValidationInfo) -> str:
        source = (info.context or {}).get("source")
        if source is not None and _normalize(value) not in _normalize(source):
            raise ValueError(
                "evidence nie jest dosłownym cytatem z kodu źródłowego "
                f"(otrzymano: {value[:120]!r}). Skopiuj fragment kodu dokładnie, bez numerów linii."
            )
        return value


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION)
    file: str = Field(description="Ścieżka recenzowanego pliku.")
    summary: str = Field(min_length=10, description="Ogólna ocena pliku w 1-3 zdaniach.")
    findings: list[Finding] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_findings(self, info: ValidationInfo) -> "Review":
        ids = [f.id for f in self.findings]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"Zduplikowane id uwag: {sorted(dupes)}")
        source = (info.context or {}).get("source")
        if source is not None:
            n_lines = len(source.splitlines()) or 1
            for f in self.findings:
                if f.line_end > n_lines:
                    raise ValueError(f"{f.id}: line_end={f.line_end} wykracza poza plik ({n_lines} linii)")
        return self


def review_json_schema() -> dict[str, Any]:
    return Review.model_json_schema()


def export_schemas(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in (("review", Review), ("finding", Finding)):
        path = out_dir / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(path)
    return written
