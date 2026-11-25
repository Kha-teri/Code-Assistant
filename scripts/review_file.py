"""Recenzja jednego lub kilku plików i wypisanie zwalidowanego JSON.

Przykłady:
    python scripts/review_file.py examples/smoke/inventory.py
    python scripts/review_file.py examples/smoke/*.py examples/smoke/*.js --out outputs/smoke
    python scripts/review_file.py plik.py --model nvidia/nemotron-3-ultra-550b-a55b:free --lang en
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code_assistant.config import Settings  # noqa: E402
from code_assistant.llm import LLMClient  # noqa: E402
from code_assistant.review import ReviewFailed, review_file  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--lang", default="pl", help="język uwag: pl | en (domyślnie pl)")
    p.add_argument("--model")
    p.add_argument("--temperature", type=float)
    p.add_argument("--max-tokens", type=int)
    p.add_argument("--out", type=Path, help="katalog na wyniki <plik>.review.json (oraz surowe odpowiedzi)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    for noisy in ("httpx", "openai", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    settings = Settings.from_env()
    overrides = {
        k: v
        for k, v in {"model": args.model, "temperature": args.temperature, "max_tokens": args.max_tokens}.items()
        if v is not None
    }
    settings = dataclasses.replace(settings, **overrides)
    client = LLMClient(settings)

    failures = 0
    for path in args.files:
        try:
            result = review_file(client, path, language=args.lang)
        except ReviewFailed as exc:
            failures += 1
            logging.error("%s: %s", path, exc)
            if args.out:
                _dump_raw(args.out, path, [a.__dict__ for a in exc.attempts])
            continue

        payload = result.review.model_dump(mode="json")
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / f"{path.name}.review.json").write_text(text, encoding="utf-8")
            _dump_raw(args.out, path, [a.__dict__ for a in result.attempts])
        else:
            print(text)
        logging.info(
            "%s: %d uwag, prób=%d, tokeny=%d (prompt=%d, completion=%d)",
            path, len(result.review.findings), len(result.attempts), result.usage.total_tokens,
            result.usage.prompt_tokens, result.usage.completion_tokens,
        )

    u = client.total_usage
    logging.info("SUMA: wywołań=%d, tokeny=%d (prompt=%d, completion=%d)", u.calls, u.total_tokens,
                 u.prompt_tokens, u.completion_tokens)
    return 1 if failures else 0


def _dump_raw(out: Path, path: Path, attempts: list[dict]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{path.name}.attempts.json").write_text(
        json.dumps(attempts, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    raise SystemExit(main())
