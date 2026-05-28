"""
Listing 3.14 (extended): catalog/main.py

The chapter 2 catalog service, upgraded with:
  - structured error envelope (Listing 3.13)
  - confidence-carrying search response (Listing 3.6 / 3.14)
  - the complete OpenAPI 3.1 spec from Listing 3.12 served at /openapi.json
  - getProduct endpoint surfacing structured 404s

Run:
  uvicorn main:app --host 0.0.0.0 --port 8080
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import asyncpg
import os
import yaml
from fastapi import FastAPI, Query

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
# OpenAPI: serve the hand-written spec from openapi.yaml at /openapi.json,
# overriding FastAPI's auto-generated one. The chapter argues that the
# producing team should treat the spec as a first-class artefact, derived
# from code where possible but always reviewed; here we serve a hand-curated
# version that meets the standard of Listing 3.12.
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
# This is the chapter 2 substring search wrapped in the confidence-carrying
# envelope of Listing 3.6. The retrieval is unchanged; what is added is the
# decision block declaring that the deterministic fallback strategy is the
# one in use. When chapter 4 swaps in the semantic implementation, the
# contract does not change — only the strategy / confidence / fallback_used
# fields take on new values.
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
# A liveness probe is handy when running under docker-compose with a
# healthcheck. Not part of the chapter; not in the spec.
# ---------------------------------------------------------------------------
@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"ok": True}
