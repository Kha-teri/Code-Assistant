import json
from types import SimpleNamespace

import pytest

from code_assistant.config import Settings
from code_assistant.llm.client import LLMClient
from code_assistant.prompts import reviewer_system_prompt
from code_assistant.review import ReviewFailed, extract_json, number_lines, review_file

CODE = "def f(x):\n    return x / 0\n"
GOOD = {
    "file": "ignored-by-parser.py",
    "summary": "Funkcja zawsze rzuca wyjątek.",
    "findings": [{
        "id": "F1", "category": "bug", "severity": "high", "title": "Dzielenie przez zero",
        "line_start": 2, "line_end": 2, "evidence": "return x / 0",
        "explanation": "Każde wywołanie kończy się ZeroDivisionError.", "suggestion": "Popraw dzielnik.",
        "confidence": 0.9,
    }],
}


class FakeCompletions:
    """Imituje openai.chat.completions, zwracając kolejne zaprogramowane odpowiedzi."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.replies.pop(0)
        return SimpleNamespace(
            model=kwargs["model"],
            choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50, completion_tokens_details=None),
        )


def make_client(replies, **settings):
    fake = FakeCompletions(replies)
    client = LLMClient(Settings(api_key="test", **settings),
                       openai_client=SimpleNamespace(chat=SimpleNamespace(completions=fake)))
    return client, fake


@pytest.fixture
def src(tmp_path):
    p = tmp_path / "a.py"
    p.write_text(CODE, encoding="utf-8")
    return p


def test_success_first_try(src):
    client, fake = make_client([json.dumps(GOOD)])
    res = review_file(client, src)
    assert len(res.attempts) == 1
    assert res.review.file == src.as_posix()
    assert res.usage.total_tokens == 150
    assert "response_format" not in fake.calls[0]


def test_retry_after_invalid_json_and_bad_evidence(src):
    bad_evidence = json.loads(json.dumps(GOOD))
    bad_evidence["findings"][0]["evidence"] = "return x / zero"
    client, fake = make_client(["not json at all", json.dumps(bad_evidence), "```json\n" + json.dumps(GOOD) + "\n```"])
    res = review_file(client, src)
    assert [a.error is None for a in res.attempts] == [False, False, True]
    # feedback o błędzie trafia do kolejnej próby
    last_messages = fake.calls[2]["messages"]
    assert "evidence" in last_messages[-1]["content"]
    assert client.total_usage.calls == 3


def test_gives_up_after_max_attempts(src):
    client, _ = make_client(["{}", "{}"])
    with pytest.raises(ReviewFailed) as exc:
        review_file(client, src, max_attempts=2)
    assert len(exc.value.attempts) == 2


def test_json_schema_response_format(src):
    client, fake = make_client([json.dumps(GOOD)], response_format="json_schema")
    review_file(client, src)
    rf = fake.calls[0]["response_format"]
    assert rf["type"] == "json_schema" and rf["json_schema"]["schema"]["title"] == "Review"


def test_extract_json_with_prose():
    assert json.loads(extract_json('Here you go:\n{"a": 1}\nThanks')) == {"a": 1}


def test_number_lines():
    assert number_lines("a\nb") == "1 | a\n2 | b"


def test_prompt_contains_schema_and_language():
    prompt = reviewer_system_prompt("pl")
    assert "Polish" in prompt and '"title":"Review"' in prompt and "{schema}" not in prompt
