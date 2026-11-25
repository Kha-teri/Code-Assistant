"""Spójność zestawu przykładów: ground truth musi wskazywać istniejące linie i dosłowne cytaty."""

import json
from pathlib import Path

import pytest

from code_assistant.schema import Category, Severity

SNIPPETS = Path(__file__).resolve().parent.parent / "examples" / "snippets"
MANIFEST = json.loads((SNIPPETS / "manifest.json").read_text(encoding="utf-8"))


def test_ten_snippets_all_present():
    files = [s["file"] for s in MANIFEST["snippets"]]
    assert len(files) == 10 == len(set(files))
    on_disk = {p.name for p in SNIPPETS.iterdir() if p.name != "manifest.json"}
    assert set(files) == on_disk


def test_has_clean_controls_and_all_categories():
    assert sum(1 for s in MANIFEST["snippets"] if not s["expected"]) >= 2
    cats = {e["category"] for s in MANIFEST["snippets"] for e in s["expected"]}
    assert cats == {c.value for c in Category}


@pytest.mark.parametrize("snippet", MANIFEST["snippets"], ids=lambda s: s["file"])
def test_expected_points_at_evidence(snippet):
    lines = (SNIPPETS / snippet["file"]).read_text(encoding="utf-8").splitlines()
    for e in snippet["expected"]:
        Category(e["category"]), Severity(e["severity"])
        region = "\n".join(lines[e["line_start"] - 1 : e["line_end"]])
        assert e["evidence"] in region, f"{snippet['file']}: {e['evidence']!r} nie ma w liniach {e['line_start']}-{e['line_end']}"
