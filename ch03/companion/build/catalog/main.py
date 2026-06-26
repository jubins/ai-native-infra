"""
Listings 3.18 / 3.19 — catalog/main.py

Chapter 2 (Listing 2.11) introduced this service with two bare endpoints:
  - GET /catalog/products/{id}  — exact match returning a raw dict or {"error": "not found"}
  - GET /catalog/search?q=      — ILIKE substring search returning a bare list

This chapter upgrades each of those without changing the contract shape that
downstream consumers depend on:
  - Structured error envelope (Listing 3.16) replaces bare {"error": ...} strings
  - Confidence-carrying decision block (Listing 3.19) wraps the search response
  - Hand-curated OpenAPI 3.1 spec (Listing 3.15) served at /openapi.json
  - AI-powered /describe route (Listing 3.18) added as a new capability

Run:
  uvicorn main:app --host 0.0.0.0 --port 8080
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import asyncpg
import os
import yaml
from fastapi import Body, FastAPI, Query

from describe import generate_description                        #A
from errors import APIError, install_error_handlers


pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the connection pool on startup; close it on shutdown."""
    global pool
    pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=1,
        max_size=10,
    )
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="catalog", lifespan=lifespan)
install_error_handlers(app)


# ---------------------------------------------------------------------------
# OpenAPI: chapter 2 had no spec. Here the hand-written openapi.yaml
# (Listing 3.15) replaces FastAPI's auto-generated one, treating the spec
# as a first-class artefact that an autonomous consumer can discover at runtime.
# ---------------------------------------------------------------------------
_SPEC_PATH = Path(__file__).parent / "openapi.yaml"
_SPEC_CACHE: Optional[dict] = None


def _load_spec() -> dict:
    global _SPEC_CACHE
    if _SPEC_CACHE is None:
        with _SPEC_PATH.open("r", encoding="utf-8") as f:
            _SPEC_CACHE = yaml.safe_load(f)
    return _SPEC_CACHE


def _custom_openapi():
    return _load_spec()


app.openapi = _custom_openapi


# ---------------------------------------------------------------------------
# /catalog/products/{product_id}
# ---------------------------------------------------------------------------
@app.get("/catalog/products/{product_id}")
async def get_product(product_id: str):
    if not product_id.startswith("p_") or not product_id[2:].isdigit():
        # The OpenAPI spec declares the pattern; we mirror it here so the
        # error envelope carries the field name and a useful hint.
        raise APIError(
            status_code=422,
            error_code="INVALID_PRODUCT_ID",
            type="validation_error",
            message=f"Product identifier {product_id!r} is malformed.",
            field="product_id",
            hint="Identifiers match the pattern '^p_[0-9]+$', e.g. p_001.",
            retryable=False,
        )

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, price_cents, description "
            "FROM products WHERE id = $1",
            product_id,
        )

    if row is None:
        raise APIError(
            status_code=404,
            error_code="PRODUCT_NOT_FOUND",
            type="validation_error",
            message=f"No product exists with identifier {product_id}",
            field="product_id",
            retryable=False,
        )

    return {
        "id": row["id"],
        "name": row["name"],
        "price_cents": row["price_cents"],
        "description": row["description"],
    }


# ---------------------------------------------------------------------------
# /catalog/search
#
# Chapter 2 (Listing 2.11) returned a bare list from an ILIKE query.
# The ILIKE retrieval is unchanged here; what is added is the decision block
# (Listing 3.19) so callers know the strategy and confidence in use.
# When a later chapter swaps in semantic search, only those fields change —
# the response shape stays the same.
# ---------------------------------------------------------------------------
@app.get("/catalog/search")
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, price_cents, description FROM products "
            "WHERE name ILIKE $1 OR description ILIKE $1 LIMIT $2",
            f"%{q}%",
            limit,
        )

    results = [
        {
            "id": r["id"],
            "name": r["name"],
            "price_cents": r["price_cents"],
            "description": r["description"],
            "match_score": None,    # null on the deterministic fallback path
        }
        for r in rows
    ]

    return {
        "results": results,
        "decision": {
            "strategy": "keyword_ilike",
            "confidence": None,
            "fallback_used": True,
            "fallback_strategy": "keyword_ilike",
        },
    }


# ---------------------------------------------------------------------------
# /catalog/products/{product_id}/describe  (Listing 3.18)
#
# New in chapter 3. Chapter 2 had no description generation — products carried
# only static text. This route calls Gemini to produce a natural-language
# description; describe.py owns generation, confidence evaluation, and fallback.
# ---------------------------------------------------------------------------
@app.post("/catalog/products/{product_id}/describe")
async def describe_product(
    product_id: str,
    body: dict = Body(default={}),                               #B
):
    tone = body.get("tone", "professional")
    if tone not in ("professional", "casual"):
        raise APIError(422, "INVALID_TONE", "validation_error",  #C
                       "tone must be 'professional' or 'casual'.",
                       field="tone", retryable=False)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, price_cents, description, category "
            "FROM products WHERE id = $1", product_id)

    if row is None:
        raise APIError(404, "PRODUCT_NOT_FOUND", "validation_error", #D
                       f"No product exists with identifier {product_id}.",
                       field="product_id", retryable=False)

    result = await generate_description(dict(row), tone)
    return {"product_id": product_id, "tone": tone, **result}    #E

#A Separation of API and generation logic.
#B Optional request body; defaults to professional tone when omitted.
#C Early validation using the standard error path.
#D Non-retryable 404 for unknown products.
#E Direct propagation of generation result and decision metadata.


# ---------------------------------------------------------------------------
# A liveness probe is handy when running under docker-compose with a
# healthcheck. Not part of the chapter; not in the spec.
# ---------------------------------------------------------------------------
@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"ok": True}
