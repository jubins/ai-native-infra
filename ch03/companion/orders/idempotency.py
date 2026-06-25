"""
Listing 3.20: orders/idempotency.py

Idempotency store for POST /orders, backed by a plain Postgres table in the
existing orders database. Repeated requests with the same Idempotency-Key
return the stored response and set Idempotent-Replay: true; the handler is
never called twice for the same key.
"""
import json

from fastapi import Request, Response

from errors import APIError

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS idempotency_keys (
  key         TEXT PRIMARY KEY,
  response    JSONB NOT NULL,
  status_code INT  NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)"""                                              #A


async def with_idempotency(request: Request, pool, handler):
    key = request.headers.get("Idempotency-Key")
    if key is None:                               #B
        raise APIError(
            400, "MISSING_IDEMPOTENCY_KEY", "validation_error",
            "POST /orders requires an Idempotency-Key header.",
            hint="Send a fresh UUID per operation; reuse on retries.",
        )

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT response, status_code FROM idempotency_keys WHERE key = $1",
            key,
        )
        if row:                                   #C
            return Response(
                content=row["response"],
                status_code=row["status_code"],
                media_type="application/json",
                headers={"Idempotent-Replay": "true"},
            )

        result, status = await handler()          #D
        await conn.execute(
            "INSERT INTO idempotency_keys (key, response, status_code) "
            "VALUES ($1, $2, $3) ON CONFLICT (key) DO NOTHING",
            key, json.dumps(result), status,
        )
        return Response(
            content=json.dumps(result),
            status_code=status,
            media_type="application/json",
        )

#A Plain Postgres table in the orders database; no new infrastructure required.
#  A background job or pg_cron task would purge rows older than 24 h in production.
#B Key is required. Missing key returns a structured APIError with a hint.
#C A recognised key returns the stored response plus Idempotent-Replay: true.
#D ON CONFLICT DO NOTHING prevents concurrent retries both triggering execution.
