# Chapter 3 — API Design and Contract Evolution

Companion code for chapter 3 of *AI-Native Infrastructure*.

## How this relates to chapter 2

Chapter 2 built a skeleton platform: a gateway routing to three services
(catalog, checkout, orders) backed by a single Postgres instance. The catalog
used a plain ILIKE search — intentionally limited.

Chapter 3 upgrades the catalog service and adds a new orders service with
patterns that make both APIs usable by autonomous consumers. The `build/`
folder here replaces the chapter 2 skeleton: you bring down the chapter 2
stack and bring this one up instead.

What changed from the chapter 2 catalog:

| What | Chapter 2 | Chapter 3 |
| ---- | --------- | --------- |
| Error responses | `{"error": "not found"}` | Five-field structured envelope (Listing 3.16) |
| Search response | bare list of products | Confidence-carrying `decision` block (Listing 3.19) |
| OpenAPI spec | none | Complete OpenAPI 3.1 spec served at `/openapi.json` (Listing 3.15) |
| Product descriptions | static text only | AI-generated via Gemini with static fallback (Listings 3.17–3.18) |

What is new in chapter 3:

- **Orders service** — `POST /orders` with idempotency keys (Listing 3.20), its own Postgres instance, and a machine-readable changelog (section 3.7.6).
- The gateway and checkout services from chapter 2 are not used in this chapter — the focus is the catalog–orders pair and the contract patterns between them.

> **To run:** bring down the chapter 2 stack first (`cd ch02/companion/build && docker compose -f listing_2_9_docker_compose.yml down`), then follow the Quickstart below.

---

## Structure

```
ch03/companion/
├── listings/                                         # standalone concept listings (3.1–3.14)
│   ├── listing_3_1_tool_definition.json              # self-describing tool example
│   ├── listing_3_2_error_response_compared.json      # opaque vs. recoverable error
│   ├── listing_3_3_catalog_openapi_compared.yaml     # loose vs. complete OpenAPI
│   ├── listing_3_4_orders_descriptions_compared.yaml # insufficient vs. sufficient descriptions
│   ├── listing_3_5_discovery_calls.sh                # runtime schema discovery (REST/GraphQL/gRPC)
│   ├── listing_3_6_order_response_compared.txt       # field-varying vs. deterministic response
│   ├── listing_3_7_order.proto                       # deterministic shape in gRPC/proto3
│   ├── listing_3_8_error_envelope.json               # five-field error envelope (422 + 503)
│   ├── listing_3_9_error_extensions.json             # five fields inside a GraphQL extensions object
│   ├── listing_3_10_search_response_with_confidence.json  # confidence-carrying search response
│   ├── listing_3_11_idempotent_post.txt              # write with idempotency key + replay
│   ├── listing_3_12_recoverable_writes.txt           # soft delete + approval checkpoint
│   ├── listing_3_13_deprecation_in_openapi.yaml      # two-stage field rename
│   └── listing_3_14_changelog_machine.json           # machine-readable changelog format
└── build/                                            # runnable platform (section 3.7, Listings 3.15–3.21)
    ├── catalog/
    │   ├── main.py          # Listings 3.18 + 3.19 — /describe route + search endpoint
    │   ├── errors.py        # Listing 3.16 — structured-error middleware
    │   ├── describe.py      # Listing 3.17 — Gemini description with static fallback
    │   ├── openapi.yaml     # Listing 3.15 — complete OpenAPI 3.1 spec
    │   ├── db_init.sql      # products schema + seed data (same four products as ch02)
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
    ├── listing_3_15_docker_compose.yml  # postgres (catalog) + postgres (orders) + catalog + orders
    ├── listing_3_21_smoke_tests.sh      # seven checks covering all patterns
    ├── Makefile
    └── .env.example
```

---

## Standalone concept listings (sections 3.2–3.6)

These files are illustrative — they show the JSON, YAML, or shell commands
discussed in each section. Read them alongside the chapter text; they do not
need to be executed (except `listing_3_5_discovery_calls.sh`, which is runnable
against a live stack).

| Listing | File | Description |
| ------- | ---- | ----------- |
| 3.1 | `listings/listing_3_1_tool_definition.json` | Self-describing tool an agent can use without coordination |
| 3.2 | `listings/listing_3_2_error_response_compared.json` | Opaque vs. recoverable error format |
| 3.3 | `listings/listing_3_3_catalog_openapi_compared.yaml` | Loose vs. complete OpenAPI declaration |
| 3.4 | `listings/listing_3_4_orders_descriptions_compared.yaml` | Insufficient vs. sufficient descriptions |
| 3.5 | `listings/listing_3_5_discovery_calls.sh` | Runtime schema discovery (REST, GraphQL, gRPC) |
| 3.6 | `listings/listing_3_6_order_response_compared.txt` | Field-varying vs. deterministic response shape |
| 3.7 | `listings/listing_3_7_order.proto` | Deterministic response shape in gRPC/proto3 |
| 3.8 | `listings/listing_3_8_error_envelope.json` | Five-field error envelope (422 validation + 503 server error) |
| 3.9 | `listings/listing_3_9_error_extensions.json` | Five-field envelope inside a GraphQL `extensions` object |
| 3.10 | `listings/listing_3_10_search_response_with_confidence.json` | Confidence-carrying search response |
| 3.11 | `listings/listing_3_11_idempotent_post.txt` | Write with idempotency key + replay |
| 3.12 | `listings/listing_3_12_recoverable_writes.txt` | Soft delete + approval checkpoint |
| 3.13 | `listings/listing_3_13_deprecation_in_openapi.yaml` | Two-stage field rename in OpenAPI |
| 3.14 | `listings/listing_3_14_changelog_machine.json` | Machine-readable changelog format |

---

## Build listings — upgraded platform (section 3.7)

These listings form the running stack. Together they turn the chapter 2 catalog
into a service whose contract carries enough information that an autonomous
consumer can use it correctly with no external coordination, recognise when a
response is uncertain, and recover from errors without human intervention.

| Listing | File | Description |
| ------- | ---- | ----------- |
| 3.15 | `build/catalog/openapi.yaml` | Complete OpenAPI 3.1 specification |
| 3.16 | `build/catalog/errors.py` | Structured-error middleware |
| 3.17 | `build/catalog/describe.py` | AI-powered description endpoint (Gemini + fallback) |
| 3.18 | `build/catalog/main.py` | `/describe` route handler |
| 3.19 | `build/catalog/main.py` | Confidence-carrying search response |
| 3.20 | `build/orders/idempotency.py` | Idempotency store for POST /orders |
| 3.21 | `build/listing_3_21_smoke_tests.sh` | Seven smoke tests covering all patterns |

---

## Prerequisites

- Docker and Docker Compose
- `curl` and (recommended) `jq` for the smoke tests
- `uuidgen` (pre-installed on macOS; `sudo apt install uuid-runtime` on Linux)
- A Gemini API key for the `/describe` endpoint (falls back gracefully without one)
- Python 3.10+ if you want to run pytest locally

> **Note:** the `describe.py` endpoint (Listing 3.17) calls Gemini to generate
> product descriptions. It implements the same bounded-intelligence envelope
> introduced in chapter 2 (appendix A) — try the LLM, fall back to a static
> template on any failure — but does so inline rather than importing
> `ch02_setup.py`. The build services are self-contained Docker images; their
> dependencies live in `build/catalog/requirements.txt` and
> `build/orders/requirements.txt`, not in `appendix_a/`.

## Quickstart

```bash
cd build

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

Each call in `listing_3_21_smoke_tests.sh` corresponds to a pattern from the chapter:

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
pip install -r build/catalog/requirements.txt
cd build && make up && make test
```
