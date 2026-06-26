# Chapter 2 — Companion code

Companion folder for **Chapter 2 — First principles and architectural patterns**.

## Setup

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key-here"
```

Then run any listing directly:

```bash
python listings/listing_2_1_string_match.py
```

## Structure

```
ch02/companion/
├── listings/                          # standalone concept listings — run directly with python
│   ├── listing_2_1_string_match.py
│   ├── listing_2_2_semantic_search.py
│   └── ... (see table below)
├── build/                             # runnable platform skeleton (section 2.4, Listings 2.9–2.13)
│   ├── gateway/                       # Listing 2.10 — path-based proxy
│   ├── catalog/                       # Listing 2.11 — ILIKE catalog service
│   ├── checkout/                      # stub service
│   ├── orders/                        # stub service
│   ├── listing_2_9_docker_compose.yml # seven-container Compose stack
│   ├── listing_2_12_postgres_init.sql # three databases + seed data
│   └── listing_2_13_smoke_test.sh     # bring up and verify the skeleton
├── ch02_setup.py                      # shared scaffolding imported by the listings
└── requirements.txt
```

`ch02_setup.py` is shared scaffolding imported by most listings:

- `call_with_envelope(prompt, schema, fallback, …)` — the bounded-intelligence envelope used by every AI-native listing.
- `embed(text)` — produces a 768-dim vector via `gemini-embedding-001`.
- `Confidence` — Pydantic mixin that every structured response inherits from.
- `SAMPLE_PRODUCTS` — a tiny in-memory product catalog used by the search and storage examples.

## Standalone listings (section 2.2–2.3)

The filename includes a short slug so you can find the listing by topic without
opening the file first:

| In the chapter | File                                        | What it does                                      |
| -------------- | ------------------------------------------- | ------------------------------------------------- |
| Listing 2.1    | `ch02_setup.py`                             | Shared scaffolding — imported by other listings.  |
| Listing 2.2    | `listing_2_1_string_match.py`               | Traditional ILIKE search; returns 0 results.      |
| Listing 2.3    | `listing_2_2_semantic_search.py`            | Semantic search via embeddings; returns 3.        |
| Listing 2.4    | `listing_2_3_static_autoscaler.py`          | Static autoscaler rule; wrong both ways.          |
| Listing 2.5    | `listing_2_4_autonomous_autoscaler.py`      | Autonomous autoscaler with envelope and fallback. |
| Listing 2.6    | `listing_2_5_ranker_antipattern.py`         | Anti-pattern: ranker training on its own output.  |
| Listing 2.7    | `listing_2_6_bounded_intelligence.py`       | Bounded-intelligence envelope demo.               |
| Listing 2.8    | `listing_2_7_semantic_routing.py`           | Semantic routing.                                 |
| Listing 2.9    | `listing_2_8_adaptive_api.py`               | Adaptive API translation.                         |
| Listing 2.10   | `listing_2_9_hybrid_storage.py`             | Hybrid storage — exact + semantic side by side.   |
| Listing 2.11   | `listing_2_10_intelligent_events.py`        | Intelligent events with allowlist.                |
| Listing 2.12   | `listing_2_11_observability.py`             | Natural-language observability.                   |
| Listing 2.13   | `listing_2_12_autonomous_healing.py`        | Autonomous healing inside scope.                  |
| Listing 2.14   | `listing_2_13_adaptive_security.py`         | Adaptive security: flag, do not block.            |
| Listing 2.15   | `listing_2_14_predictive_scaling.py`        | Predictive scaling: slow write loop / fast read.  |
| Listing 2.16   | `listing_2_15_chained_calls_antipattern.py` | Anti-pattern: chained AI calls without checks.    |

## Build listings — skeleton platform (section 2.4)

The `build/` subfolder contains the seven-container platform skeleton.
Listings here are named files so you can open the exact file the chapter references:

| In the chapter | File                                          | Description                              |
| -------------- | --------------------------------------------- | ---------------------------------------- |
| Listing 2.9    | `build/listing_2_9_docker_compose.yml`        | Seven-container Compose stack            |
| Listing 2.10   | `build/gateway/main.py`                       | Path-based proxy gateway                 |
| Listing 2.11   | `build/catalog/main.py`                       | Minimal catalog service with ILIKE search|
| Listing 2.12   | `build/listing_2_12_postgres_init.sql`        | Three databases + product seed data      |
| Listing 2.13   | `build/listing_2_13_smoke_test.sh`            | Bring up and verify the skeleton         |

To bring it up:

```bash
cd build
docker compose -f listing_2_9_docker_compose.yml up -d --build
curl http://localhost:8080/health
```

Or run the smoke test end-to-end:

```bash
cd build
bash listing_2_13_smoke_test.sh
```

> **What this builds:** a gateway routing to three services (catalog, checkout,
> orders) backed by a single Postgres instance, plus Redis and Kafka wired for
> later chapters. The catalog uses a plain ILIKE search — intentionally limited
> so chapter 3 has a clear starting point to improve.

## Listings that need an API key

Listings that call Gemini (any listing using `embed` or `call_with_envelope`
without a mock) require `GEMINI_API_KEY`. Listings that demonstrate failure
modes or use mock LLMs run without a key:

- No key needed: `listing_2_1_string_match.py`, `listing_2_3_static_autoscaler.py`, `listing_2_5_ranker_antipattern.py`, `listing_2_6_bounded_intelligence.py`, `listing_2_15_chained_calls_antipattern.py`
- Key required: `listing_2_2_semantic_search.py`, `listing_2_4_autonomous_autoscaler.py`, `listing_2_7_semantic_routing.py` through `listing_2_14_predictive_scaling.py`

If the LLM call fails for any reason (no key, network, rate limit, malformed
response, low confidence), the envelope falls back to the deterministic path
defined per listing, and the script still produces output. This is the
bounded-intelligence principle in action.
