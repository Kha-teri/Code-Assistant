import json

import pytest
from pydantic import ValidationError

from code_assistant.schema import Review, export_schemas

SOURCE = "def f(x):\n    return x / 0\n"


def finding(**over):
    base = {
        "id": "F1", "category": "bug", "severity": "high", "title": "Dzielenie przez zero",
        "line_start": 2, "line_end": 2, "evidence": "return x / 0",
        "explanation": "Funkcja zawsze rzuca ZeroDivisionError.", "suggestion": "Usuń dzielenie.",
        "confidence": 0.95,
    }
    base.update(over)
    return base


def review(*findings):
    return {"file": "a.py", "summary": "Plik zawiera oczywisty błąd.", "findings": list(findings)}


def test_valid_review_with_source_context():
    r = Review.model_validate(review(finding()), context={"source": SOURCE})
    assert r.findings[0].severity.rank == 3


def test_evidence_must_be_verbatim():
    with pytest.raises(ValidationError, match="evidence"):
        Review.model_validate(review(finding(evidence="return x // 0")), context={"source": SOURCE})


def test_evidence_whitespace_tolerant():
    Review.model_validate(review(finding(evidence="return   x / 0")), context={"source": SOURCE})


def test_line_out_of_file():
    with pytest.raises(ValidationError, match="wykracza"):
        Review.model_validate(review(finding(line_start=9, line_end=9)), context={"source": SOURCE})


@pytest.mark.parametrize("over", [
    {"category": "style"}, {"severity": "blocker"}, {"confidence": 1.5},
    {"line_start": 2, "line_end": 1}, {"id": "1"}, {"unexpected": "x"},
])
def test_invalid_findings_rejected(over):
    with pytest.raises(ValidationError):
        Review.model_validate(review(finding(**over)))


def test_duplicate_ids():
    with pytest.raises(ValidationError, match="Zduplikowane"):
        Review.model_validate(review(finding(), finding()))


def test_empty_findings_is_valid():
    assert Review.model_validate(review()).findings == []


def test_export_schemas(tmp_path):
    paths = export_schemas(tmp_path)
    schema = json.loads(paths[0].read_text(encoding="utf-8"))
    assert schema["title"] == "Review"
    assert set(schema["$defs"]["Category"]["enum"]) == {"bug", "readability", "performance", "testing", "security"}
