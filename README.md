# Asystent przeglądu kodu

Aplikacja zwracająca ustrukturyzowaną i uzasadnioną recenzję kodu (błędy, czytelność,
wydajność, testy, bezpieczeństwo) z kontrolą fałszywych alarmów. Model: **Nemotron 3 Ultra**
(`nvidia/nemotron-3-ultra-550b-a55b`) przez OpenRouter.

Docelowy pipeline: **recenzja → samokrytyka (osobna konwersacja) → priorytetyzacja**, GUI w PySide6.
Ten etap (krok 1) obejmuje fundament: klient API, schemat, pierwszy prompt i skrypt dla jednego pliku.

## Instalacja

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env   # uzupełnij OPENROUTER_API_KEY
```

## Użycie

```powershell
.venv\Scripts\python scripts\review_file.py examples\smoke\inventory.py
.venv\Scripts\python scripts\review_file.py examples\smoke\inventory.py examples\smoke\auth.py examples\smoke\stats.js --out outputs\smoke
.venv\Scripts\python scripts\export_schema.py
.venv\Scripts\python -m pytest -q
```

## Struktura

| Ścieżka | Opis |
|---|---|
| `code_assistant/config.py` | Ustawienia z `.env` (model, temperatura, limit tokenów, tryb `response_format`, liczba prób) |
| `code_assistant/llm/client.py` | Klient OpenRouter; każde wywołanie to niezależna konwersacja; logowanie tokenów (w tym reasoning) |
| `code_assistant/schema.py` | Modele `Finding` i `Review` (Pydantic) + eksport JSON Schema; walidacja dosłowności `evidence` względem kodu |
| `code_assistant/prompts/reviewer_system.md` | Prompt systemowy recenzenta: rola, 5 kategorii, skala ważności, reguły dowodów, JSON-only |
| `code_assistant/review.py` | Recenzja pliku: numerowanie linii, parsowanie, walidacja i ponawianie z informacją o błędzie |
| `scripts/review_file.py` | CLI: zwraca zwalidowany JSON dla jednego lub wielu plików |
| `schemas/` | Wyeksportowane JSON Schema |
| `examples/smoke/` | 3 pliki z oczywistymi błędami do ręcznego testu promptu |
| `examples/snippets/` | Zestaw 10 przykładów + `manifest.json` z oczekiwanymi uwagami (2 pliki „czyste” jako kontrola fałszywych alarmów) |

## Kontrola jakości odpowiedzi

- Walidacja Pydantic działa **zawsze**, niezależnie od `CA_RESPONSE_FORMAT` (`none` / `json_object` / `json_schema`).
- `evidence` musi być dosłownym cytatem z pliku, a linie muszą mieścić się w pliku — inaczej odpowiedź jest odrzucana.
- Przy błędzie model dostaje listę błędów walidacji i jest proszony o poprawiony JSON (domyślnie do 3 prób).
