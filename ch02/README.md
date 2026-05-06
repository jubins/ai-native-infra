# Chapter 2 — Companion code

Companion folder for **Chapter 2 — First principles and architectural patterns**.

## Setup

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key-here"
```

For a fully frozen install (e.g. CI, or to reproduce exactly the versions the
book was written against), use the lock file instead:

```bash
pip install -r requirements-lock.txt
```

Then run any listing directly:

```bash
python listing_2_1.py
```

## Structure

`ch02_setup.py` is shared scaffolding imported by most listings:

- `call_with_envelope(prompt, schema, fallback, …)` — the bounded-intelligence envelope used by every AI-native listing.
- `embed(text)` — produces a 768-dim vector via `gemini-embedding-001`.
- `Confidence` — Pydantic mixin that every structured response inherits from.
- `SAMPLE_PRODUCTS` — a tiny in-memory product catalog used by the search and storage examples.

## Listings

The mapping from listings in the chapter to files in this folder:

| In the chapter | File                | What it does                                      |
| -------------- | ------------------- | ------------------------------------------------- |
| Listing 2.1    | `ch02_setup.py`     | Shared scaffolding — imported by other listings.  |
| Listing 2.2    | `listing_2_1.py`    | Traditional ILIKE search; returns 0 results.      |
| Listing 2.3    | `listing_2_2.py`    | Semantic search via embeddings; returns 3.       |
| Listing 2.4    | `listing_2_3.py`    | Static autoscaler rule; wrong both ways.         |
| Listing 2.5    | `listing_2_4.py`    | Autonomous autoscaler with envelope and fallback. |
| Listing 2.6    | `listing_2_5.py`    | Anti-pattern: ranker training on its own output. |
| Listing 2.7    | `listing_2_6.py`    | Bounded-intelligence envelope demo.              |
| Listing 2.8    | `listing_2_7.py`    | Semantic routing.                                 |
| Listing 2.9    | `listing_2_8.py`    | Adaptive API translation.                         |
| Listing 2.10   | `listing_2_9.py`    | Hybrid storage — exact + semantic side by side.   |
| Listing 2.11   | `listing_2_10.py`   | Intelligent events with allowlist.                |
| Listing 2.12   | `listing_2_11.py`   | Natural-language observability.                   |
| Listing 2.13   | `listing_2_12.py`   | Autonomous healing inside scope.                  |
| Listing 2.14   | `listing_2_13.py`   | Adaptive security: flag, do not block.            |
| Listing 2.15   | `listing_2_14.py`   | Anti-pattern: chained AI calls without checks.   |

## Skeleton platform (section 2.7)

The `skeleton/` subfolder will hold the platform skeleton from section 2.7
(gateway, catalog, checkout, orders services, plus the Compose file). To bring
it up:

```bash
cd skeleton/compose
docker compose up -d --build
curl http://localhost:8080/health
```

## Listings that need an API key

Listings that call Gemini (any listing using `embed` or `call_with_envelope`
without a mock) require `GEMINI_API_KEY`. Listings that demonstrate failure
modes or use mock LLMs run without a key:

- No key needed: `listing_2_1.py`, `listing_2_3.py`, `listing_2_5.py`, `listing_2_6.py`, `listing_2_14.py`
- Key required: `listing_2_2.py`, `listing_2_4.py`, `listing_2_7.py` through `listing_2_13.py`

If the LLM call fails for any reason (no key, network, rate limit, malformed
response, low confidence), the envelope falls back to the deterministic path
defined per listing, and the script still produces output. This is the
bounded-intelligence principle in action.
