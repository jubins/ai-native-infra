# orders/main.py
# Minimal orders service.  Owns the orders schema in Postgres.
# Exposes two endpoints: list orders for a customer, and get a
# single order by ID.  Fulfillment logic is out of scope for the
# skeleton; this service exists to complete the three-service topology.

from fastapi import FastAPI
import asyncpg
import os

app = FastAPI(title="orders")
pool = None


@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "orders"}


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, customer_id, status, created_at "
            "FROM orders WHERE id = $1",
            order_id,
        )
        return dict(row) if row else {"error": "not found"}


@app.get("/orders")
async def list_orders(customer_id: str, limit: int = 20):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, customer_id, status, created_at "
            "FROM orders WHERE customer_id = $1 "
            "ORDER BY created_at DESC LIMIT $2",
            customer_id,
            limit,
        )
        return [dict(r) for r in rows]
