# listing_2_16 — gateway/main.py
# A deliberately traditional path-based proxy.
# Every routing rule is in the ROUTES table; there is no dynamic
# decision-making.  This is the control in the experiment: when
# semantic routing is introduced in a later chapter, the difference
# will be visible against this baseline.

from fastapi import FastAPI, Request, HTTPException
import httpx
import os

app = FastAPI(title="ecommerce-gateway")

ROUTES = {                                        # A
    "/catalog":  os.environ["CATALOG_URL"],
    "/checkout": os.environ["CHECKOUT_URL"],
    "/orders":   os.environ["ORDERS_URL"],
}


@app.get("/health")                               # B
def health():
    return {"status": "ok"}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(full_path: str, request: Request):
    for prefix, upstream in ROUTES.items():       # C
        if ("/" + full_path).startswith(prefix):
            url = f"{upstream}/{full_path}"
            async with httpx.AsyncClient(timeout=5.0) as client:  # D
                body = await request.body()
                resp = await client.request(
                    request.method,
                    url,
                    headers={
                        k: v for k, v in request.headers.items()
                        if k.lower() not in ("host", "content-length")  # E
                    },
                    content=body,
                )
                if resp.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    return resp.json()
                return resp.text

    raise HTTPException(status_code=404, detail="no route")       # F


# A — The routing table: three path prefixes mapped to upstream URLs read
#     from the environment.  This is the entire routing logic.
# B — Health endpoint kept separate from the catch-all so the gateway can
#     report liveness without forwarding to any upstream.
# C — First prefix to match wins; list longer prefixes first if they overlap.
# D — Hard timeout on every upstream call; without it a slow upstream ties up
#     gateway workers indefinitely.
# E — Strip hop-by-hop headers: Host (httpx sets its own) and Content-Length
#     (recomputed for the forwarded request).
# F — Return 404 rather than a confusing 502 when no prefix matches.
