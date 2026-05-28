# Chapter 3 — API Design and Contract Evolution

Companion code for chapter 3 of *AI-Native Infrastructure*. This directory
extends the chapter 2 catalog service with the three artefacts described in
section 3.8:

1. A complete OpenAPI 3.1 specification (`catalog/openapi.yaml`, Listing 3.12)
2. Structured-error middleware (`catalog/errors.py`, Listing 3.13)
3. A confidence-carrying search response (`catalog/main.py`, Listing 3.14)

Together they turn the chapter 2 catalog into a service whose contract is a
*semantic contract* in the sense of section 3.7: a contract carrying enough
information that an autonomous consumer can use the API correctly with no
external coordination, recognise when a response is uncertain, and recover
from errors without human intervention.

The companion stack is self-contained — it ships its own Postgres so you can
run it without the rest of the chapter 2 platform.

## Prerequisites

- Docker and Docker Compose
- `curl` and (recommended) `jq` for the smoke tests
- Python 3.10+ if you want to run pytest locally

## Quickstart

```bash
make up        # build + start postgres and catalog
make smoke     # run the four smoke tests from Listing 3.15
make down      # stop the services
```

The catalog service listens on `http://localhost:8080`. Postgres is exposed
on `5432` for inspection.

## What the smoke tests demonstrate

Each call in `smoke_tests.sh` corresponds to one of the chapter 3 patterns:

| # | Call                              | Pattern from the chapter                          |
| - | --------------------------------- | ------------------------------------------------- |
| 1 | `GET /openapi.json`               | Pattern 3 — schema discovery at runtime            |
| 2 | `GET /catalog/search?q=jacket`    | Pattern 6 — confidence-carrying response           |
| 3 | `GET /catalog/search?q=`          | Pattern 5 — structured error (framework path)     |
| 4 | `GET /catalog/products/p_999`     | Pattern 5 — structured error (application path)   |

## Running pytest

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r catalog/requirements.txt
make up
make test
```

The test suite in `tests/test_smoke.py` covers the same four patterns plus a
few extra assertions that lock in the deterministic-shape rules of Listing
3.4 and the OpenAPI completeness rules of section 3.3.

## Layout

```
ch03/companion/
├── catalog/
│   ├── main.py          # Listing 3.14 — search endpoint with decision block
│   ├── errors.py        # Listing 3.13 — structured-error middleware
│   ├── openapi.yaml     # Listing 3.12 — complete OpenAPI 3.1 spec
│   ├── db_init.sql      # products schema + seed data
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   └── test_smoke.py    # pytest equivalent of smoke_tests.sh
├── docker-compose.yml   # postgres + catalog
├── smoke_tests.sh       # Listing 3.15
├── discovery_calls.sh   # Listing 3.3 (REST runnable; GraphQL/gRPC reference)
├── Makefile
└── README.md
```

## Using your existing chapter 2 Postgres

If you already have the chapter 2 platform running and want this service to
talk to it instead of the bundled Postgres, comment the `postgres:` service
out of `docker-compose.yml` and point `DATABASE_URL` at the existing
instance:

```yaml
catalog:
  environment:
    DATABASE_URL: postgresql://catalog:catalog@host.docker.internal:5432/catalog
```

The schema in `catalog/db_init.sql` should match what chapter 2 set up; if
not, run that file against your chapter 2 database first.

## What chapter 4 will add

Chapter 4 introduces the semantic routing layer that consumes the OpenAPI
specifications written here. The `x-confidence-aware` and `x-fallback-strategy`
extensions on `/catalog/search` are the hooks the router will read. Nothing
in the chapter 3 contract needs to change when the semantic implementation
replaces the substring search — the `strategy`, `confidence`, and
`fallback_used` fields simply take on new values.
