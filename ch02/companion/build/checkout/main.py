# checkout/main.py
# Minimal checkout service.  Owns the checkout schema in Postgres.
# Accepts a cart payload and records a pending order.
# Payment logic is intentionally omitted — the focus here is the
# skeleton topology, not production checkout semantics.

from fastapi import FastAPI
from pydantic import BaseModel
import asyncpg
import os

app = FastAPI(title="checkout")
pool = None


class CartItem(BaseModel):
    product_id: str
    quantity: int


class CheckoutRequest(BaseModel):
    customer_id: str
    items: list[CartItem]


@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "checkout"}


@app.post("/checkout")
async def checkout(req: CheckoutRequest):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO orders (customer_id, status) "
            "VALUES ($1, 'pending') RETURNING id",
            req.customer_id,
        )
        return {"order_id": row["id"], "status": "pending"}
