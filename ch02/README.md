# Chapter 2 — First Principles and Architectural Patterns

![ch02](https://github.com/jubins/ai-native-infra/actions/workflows/ch02.yml/badge.svg)

Companion code for chapter 2 of *AI-Native Infrastructure*.

## Setup

The standalone listings depend on shared scaffolding in `appendix_a/`.
Install once from the repo root:

```bash
pip install -r appendix_a/requirements.txt
export GEMINI_API_KEY="your-key-here"
```

Run listings from the repo root so Python can find `ch02_setup`:

```bash
python ch02/companion/listings/listing_2_1_string_match.py
```

See `appendix_a/README.md` for details on what each key is needed for.

## Structure

```
ch02/companion/
├── listings/     # standalone concept listings — one file per chapter listing
├── bonus/        # extra runnable examples for patterns from Table 2.4
└── build/        # runnable platform skeleton (Listings 2.9–2.13)
```

## Standalone listings (sections 2.1–2.2)

Each file corresponds directly to a numbered listing in the chapter:

| Listing | File | What it does |
| ------- | ---- | ------------ |
| 2.1 | `listings/listing_2_1_string_match.py` | Traditional ILIKE search; returns 0 results for natural-language queries |
| 2.2 | `listings/listing_2_2_semantic_search.py` | Semantic search via embeddings; returns ranked results |
| 2.3 | `listings/listing_2_3_static_autoscaler.py` | Static CPU-threshold autoscaler; wrong in both directions |
| 2.4 | `listings/listing_2_4_autonomous_autoscaler.py` | Autonomous autoscaler with envelope and fallback |
| 2.5 | `listings/listing_2_5_ranker_antipattern.py` | Anti-pattern: ranker that learns from its own decisions |
| 2.6 | `listings/listing_2_6_bounded_intelligence.py` | Bounded-intelligence envelope demonstrated end-to-end |
| 2.7 | `listings/listing_2_7_semantic_routing.py` | Semantic routing: picks a service from the meaning of the request |
| 2.8 | `listings/listing_2_8_predictive_scaling.py` | Predictive scaling: slow loop writes forecast, fast loop reads it |

## Bonus listings (patterns from Table 2.4)

The chapter introduces eight infrastructure patterns; only semantic routing and
predictive scaling are developed into full numbered listings. The `bonus/`
directory contains runnable implementations of the remaining six patterns from
Table 2.4, plus one additional anti-pattern. They follow the same
bounded-intelligence structure as the chapter listings and are a useful
reference when applying these patterns in your own systems.

| File | Pattern |
| ---- | ------- |
| `bonus/adaptive_api.py` | Adaptive APIs — model maps fields by meaning across schema versions |
| `bonus/hybrid_storage.py` | Hybrid storage — exact match and semantic search side by side |
| `bonus/intelligent_events.py` | Intelligent events — priority and routing inferred from event content |
| `bonus/observability.py` | AI-native observability — natural-language question answered from telemetry |
| `bonus/autonomous_healing.py` | Autonomous healing — model proposes one action from a fixed allowlist |
| `bonus/adaptive_security.py` | Adaptive security — model flags requests that deviate from a baseline |
| `bonus/chained_calls_antipattern.py` | Anti-pattern: chained AI calls without guardrails between steps |

## Build listings — platform skeleton (section 2.4)

The `build/` directory contains the seven-container platform skeleton.
These are the files the chapter references in sections 2.4.5–2.4.9:

| Listing | File | Description |
| ------- | ---- | ----------- |
| 2.9  | `build/listing_2_9_docker_compose.yml` | Seven-container Compose stack |
| 2.10 | `build/gateway/main.py` | Path-based proxy gateway |
| 2.11 | `build/catalog/main.py` | Minimal catalog service with ILIKE search |
| 2.12 | `build/listing_2_12_postgres_init.sql` | Three databases + product seed data |
| 2.13 | `build/listing_2_13_bring_up_build.sh` | Bring up all seven containers |
| —    | `build/smoke_test.sh` | Verify the four calls from the chapter |

To bring it up:

```bash
cd ch02/companion/build
bash listing_2_13_bring_up_build.sh   # bring up all seven containers
bash smoke_test.sh                # verify the four calls from the chapter
```

> **What this builds:** a gateway routing to catalog, checkout, and orders,
> backed by a single Postgres instance, with Redis and Kafka wired for later
> chapters. The catalog uses plain ILIKE search — intentionally limited so
> chapter 3 has a clear baseline to improve on.
