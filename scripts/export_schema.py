"""Eksportuje JSON Schema modeli Review i Finding do katalogu schemas/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from code_assistant.schema import export_schemas  # noqa: E402

if __name__ == "__main__":
    for path in export_schemas(ROOT / "schemas"):
        print(path.relative_to(ROOT))
