"""
orders/main.py

Minimal orders service for the ch03 companion. Implements:
  - POST /orders   — create an order, idempotency-key required (Listing 3.20)
  - GET  /orders/{order_id} — retrieve a single order
  - OpenAPI 3.1 document served at /openapi.json
  - Structured error envelope via errors.py (Listing 3.16)

Run:
  uvicorn main:app --host 0.0.0.0 --port 8081
"""
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import asyncpg
import os
import yaml
from fastapi import FastAPI, Request

from errors import APIError, install_error_handlers
from idempotency import CREATE_TABLE, with_idempotency


pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=1,
        max_size=10,
    )
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE)           #A
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="orders", lifespan=lifespan)
install_error_handlers(app)


# ---------------------------------------------------------------------------
# OpenAPI: serve the hand-written spec at /openapi.json
# ---------------------------------------------------------------------------
_SPEC_PATH = Path(__file__).parent / "openapi.yaml"
_SPEC_CACHE: Optional[dict] = None


def _load_spec() -> dict:
    global _SPEC_CACHE
    if _SPEC_CACHE is None:
        with _SPEC_PATH.open("r", encoding="utf-8") as f:
            _SPEC_CACHE = yaml.safe_load(f)
    return _SPEC_CACHE


app.openapi = _load_spec


# ---------------------------------------------------------------------------
# POST /orders  (Listing 3.20 — wired to the idempotency store)
# ---------------------------------------------------------------------------
@app.post("/orders")
async def create_order(request: Request):
    async def handler():
        body = await request.json()

        customer_id = body.get("customer_id")
        items = body.get("items", [])

        if not customer_id:
            raise APIError(
                422, "MISSING_CUSTOMER_ID", "validation_error",
                "customer_id is required.",
                field="customer_id", retryable=False,
            )
        if not items:
            raise APIError(
                422, "MISSING_ITEMS", "validation_error",
                "items must be a non-empty list.",
                field="items", retryable=False,
            )

        async with pool.acquire() as conn:
            # Resolve price for each line item from the catalog products table.
            # In a real multi-service setup this would be an internal RPC call.
            total_cents = 0
            for item in items:
                sku = item.get("sku")
                qty = item.get("qty", 1)
                row = await conn.fetchrow(
                    "SELECT price_cents FROM products WHERE id = $1", sku
                )
                if row is None:
                    raise APIError(
                        422, "UNKNOWN_SKU", "validation_error",
                        f"Product {sku!r} does not exist.",
                        field="items.sku", retryable=False,
                    )
                total_cents += row["price_cents"] * qty

            order_id = f"ord_{uuid.uuid4().hex[:6]}"
            await conn.execute(
                "INSERT INTO orders (id, customer_id, total_cents, status) "
                "VALUES ($1, $2, $3, 'PENDING')",
                order_id, customer_id, total_cents,
            )

        result = {
            "id": order_id,
            "customer_id": customer_id,
            "status": "PENDING",
            "total_cents": total_cents,
        }
        return result, 201

    return await with_idempotency(request, pool, handler)


# ---------------------------------------------------------------------------
# GET /orders/{order_id}
# ---------------------------------------------------------------------------
@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, customer_id, total_cents, status FROM orders WHERE id = $1",
            order_id,
        )
    if row is None:
        raise APIError(
            404, "ORDER_NOT_FOUND", "validation_error",
            f"No order exists with identifier {order_id}.",
            field="order_id", retryable=False,
        )
    return dict(row)


# ---------------------------------------------------------------------------
# Liveness probe
# ---------------------------------------------------------------------------
@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"ok": True}

#A The idempotency_keys table is created at startup if it does not already exist.
#  No migration tooling required for the companion — the table is append-only.
