# listing_2_17 — catalog/main.py
# Minimal catalog service: two endpoints backed by Postgres.
#
# /catalog/products/{id}  — exact match by primary key
# /catalog/search?q=      — ILIKE substring search (intentionally defective)
#
# The ILIKE search returns zero results for queries like
# "warm jacket under $100" because it compares characters, not meaning.
# It is left in this defective form deliberately: a later chapter
# replaces it with semantic search, and the contrast matters.

from fastapi import FastAPI
import asyncpg
import os

app = FastAPI(title="catalog")
pool = None


@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "catalog"}


@app.get("/catalog/products/{product_id}")
async def get_product(product_id: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, price_cents, description "
            "FROM products WHERE id = $1",
            product_id,
        )
        return dict(row) if row else {"error": "not found"}


@app.get("/catalog/search")
async def search(q: str, limit: int = 20):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, price_cents FROM products "
            "WHERE name ILIKE $1 LIMIT $2",
            f"%{q}%",
            limit,
        )
        return [dict(r) for r in rows]
