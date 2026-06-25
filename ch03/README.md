# Chapter 3 — API Design and Contract Evolution

Companion code for chapter 3 of *AI-Native Infrastructure*. This directory
extends the chapter 2 catalog service with the nine design patterns described
in sections 3.3–3.7 and adds an orders service demonstrating idempotency.

**Listings in this chapter:**

| Listing | File | Description |
| ------- | ---- | ----------- |
| 3.15 | `catalog/openapi.yaml` | Complete OpenAPI 3.1 specification |
| 3.16 | `catalog/errors.py` | Structured-error middleware |
| 3.17 | `catalog/describe.py` | AI-powered description endpoint (Gemini + fallback) |
| 3.18 | `catalog/main.py` | `/describe` route handler |
| 3.19 | `catalog/main.py` | Confidence-carrying search response |
| 3.20 | `orders/idempotency.py` | Idempotency store for POST /orders |
| 3.21 | `smoke_tests.sh` | Seven smoke tests covering all patterns |

Together they turn the chapter 2 catalog into a service whose contract is a
*semantic contract* in the sense of section 3.7: a contract carrying enough
information that an autonomous consumer can use the API correctly with no
external coordination, recognise when a response is uncertain, and recover
from errors without human intervention.

The companion stack is self-contained — it ships its own Postgres instances so
you can run it without the rest of the chapter 2 platform.

## Prerequisites

- Docker and Docker Compose
- `curl` and (recommended) `jq` for the smoke tests
- `uuidgen` (pre-installed on macOS; `sudo apt install uuid-runtime` on Linux)
- A Gemini API key for the `/describe` endpoint (falls back gracefully without one)
- Python 3.10+ if you want to run pytest locally

## Quickstart

```bash
# Copy the example env file and add your Gemini key (optional)
cp .env.example .env
# edit .env and set GEMINI_API_KEY=your-key-here

make up      # build + start postgres (catalog), postgres (orders), catalog, orders
make smoke   # run all seven smoke tests from Listing 3.21
make down    # stop the services
```

The catalog service listens on `http://localhost:8080`.  
The orders service listens on `http://localhost:8081`.  
Catalog Postgres is exposed on `5432`; orders Postgres on `5433`.

## What the smoke tests demonstrate

Each call in `smoke_tests.sh` (Listing 3.21) corresponds to a pattern from the chapter:

| # | Call | Pattern |
| - | ---- | ------- |
| 1 | `GET /openapi.json` | Pattern 3 — schema discovery at runtime |
| 2 | `GET /catalog/search?q=jacket` | Pattern 6 — confidence-carrying response |
| 3 | `GET /catalog/search?q=` | Pattern 5 — structured error (framework path) |
| 4 | `GET /catalog/products/p_999` | Pattern 5 — structured error (application path) |
| 5 | `POST /orders` × 2, same key | Pattern 7 — idempotency replay |
| 6 | `POST /catalog/products/p_001/describe` | Pattern 6 + section 3.7.3 — AI description with decision block |
| 7 | `POST /catalog/products/p_999/describe` | Pattern 5 + section 3.7.2 — error middleware on AI route |

## The AI-powered description endpoint (section 3.7.3)

`POST /catalog/products/{product_id}/describe` calls Gemini to generate a
natural-language product description. It has two paths:

- **LLM path** — Gemini responds and passes the length check: `decision.strategy` is
  `llm_generated`, `decision.confidence` is `0.91`, `decision.fallback_used` is `false`.
- **Fallback path** — any failure (network error, quota, short response): falls back to
  a static template, `decision.fallback_used` is `true`. The caller always gets a
  usable description.

Without `GEMINI_API_KEY` set, the endpoint always takes the fallback path — the
rest of the stack works normally.

## The orders service and idempotency (section 3.7.5)

`POST /orders` requires an `Idempotency-Key` header (a client-generated UUID).
The server stores the key and response in a Postgres table; any retry with the
same key returns the stored response with `Idempotent-Replay: true` without
creating a duplicate order.

The orders service also publishes a machine-readable changelog at
`orders/changelog.json` (section 3.7.6), structured so an agent can determine
exactly what changed at each version without parsing prose release notes.

## Running pytest

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r catalog/requirements.txt
make up
make test
```

The test suite in `tests/test_smoke.py` covers the catalog patterns. See the
`CATALOG_URL` / `ORDERS_URL` environment variables in `smoke_tests.sh` to
target a non-default host.

## Layout

```
ch03/companion/
├── catalog/
│   ├── main.py          # Listings 3.18 + 3.19 — /describe route + search endpoint
│   ├── errors.py        # Listing 3.16 — structured-error middleware
│   ├── describe.py      # Listing 3.17 — Gemini description with static fallback
│   ├── openapi.yaml     # Listing 3.15 — complete OpenAPI 3.1 spec
│   ├── db_init.sql      # products schema + seed data (with category column)
│   ├── Dockerfile
│   └── requirements.txt
├── orders/
│   ├── main.py          # POST /orders + GET /orders/{id}
│   ├── errors.py        # structured-error middleware (same envelope as catalog)
│   ├── idempotency.py   # Listing 3.20 — idempotency store
│   ├── openapi.yaml     # complete OpenAPI 3.1 spec for orders
│   ├── changelog.json   # section 3.7.6 — machine-readable changelog
│   ├── db_init.sql      # orders + idempotency_keys tables + seed data
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   └── test_smoke.py    # pytest equivalent of the catalog smoke tests
├── docker-compose.yml   # postgres (catalog) + postgres (orders) + catalog + orders
├── smoke_tests.sh       # Listing 3.21 — seven checks covering all patterns
├── discovery_calls.sh   # Listing 3.5 (REST runnable; GraphQL/gRPC reference)
├── Makefile
├── .env.example
└── README.md
```