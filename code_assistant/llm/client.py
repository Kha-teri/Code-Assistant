"""Klient OpenRouter (API zgodne z OpenAI) z logowaniem zużycia tokenów."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from ..config import Settings

log = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, other: "TokenUsage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.reasoning_tokens += other.reasoning_tokens
        self.calls += other.calls


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: TokenUsage
    finish_reason: str | None = None
    latency_s: float = 0.0
    raw: Any = field(default=None, repr=False)


class LLMClient:
    """Cienka warstwa nad `openai.OpenAI` skierowana na OpenRouter.

    Każde wywołanie `chat` jest niezależną konwersacją: klient nie trzyma historii.
    Dzięki temu krytyk w kolejnych etapach może dostać osobny, czysty kontekst.
    """

    def __init__(self, settings: Settings, *, openai_client: OpenAI | None = None):
        self.settings = settings
        self._client = openai_client or OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout,
            max_retries=2,  # ponowienia transportowe (429/5xx); walidację ponawia warstwa wyżej
        )
        self.total_usage = TokenUsage()

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_schema: dict[str, Any] | None = None,
        label: str = "chat",
    ) -> LLMResponse:
        s = self.settings
        kwargs: dict[str, Any] = {
            "model": model or s.model,
            "messages": messages,
            "temperature": s.temperature if temperature is None else temperature,
            "max_tokens": max_tokens or s.max_tokens,
        }
        response_format = self._response_format(json_schema)
        if response_format is not None:
            kwargs["response_format"] = response_format
        extra_body: dict[str, Any] = {"usage": {"include": True}}
        if s.reasoning_effort:
            extra_body["reasoning"] = {"effort": s.reasoning_effort}
        kwargs["extra_body"] = extra_body

        started = time.perf_counter()
        completion = self._client.chat.completions.create(**kwargs)
        latency = time.perf_counter() - started

        usage = self._extract_usage(completion)
        self.total_usage.add(usage)
        choice = completion.choices[0]
        content = choice.message.content or ""

        log.info(
            "[%s] model=%s prompt=%d completion=%d (reasoning=%d) total=%d "
            "latency=%.1fs finish=%s | session_total=%d",
            label,
            completion.model,
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.reasoning_tokens,
            usage.total_tokens,
            latency,
            choice.finish_reason,
            self.total_usage.total_tokens,
        )
        return LLMResponse(
            content=content,
            model=completion.model,
            usage=usage,
            finish_reason=choice.finish_reason,
            latency_s=latency,
            raw=completion,
        )

    def _response_format(self, json_schema: dict[str, Any] | None) -> dict[str, Any] | None:
        mode = self.settings.response_format
        if mode == "none":
            return None
        if mode == "json_object" or json_schema is None:
            return {"type": "json_object"}
        return {
            "type": "json_schema",
            "json_schema": {"name": "review", "strict": False, "schema": json_schema},
        }

    @staticmethod
    def _extract_usage(completion: Any) -> TokenUsage:
        u = getattr(completion, "usage", None)
        if u is None:
            return TokenUsage(calls=1)
        details = getattr(u, "completion_tokens_details", None)
        reasoning = getattr(details, "reasoning_tokens", 0) if details else 0
        return TokenUsage(
            prompt_tokens=u.prompt_tokens or 0,
            completion_tokens=u.completion_tokens or 0,
            reasoning_tokens=reasoning or 0,
            calls=1,
        )
