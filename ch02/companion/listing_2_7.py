"""
listing_2_7.py — Semantic routing: pick the service from the meaning of the request.
Run: python listing_2_7.py
Requires GEMINI_API_KEY (falls back to path-based routing if unavailable).
"""
from pydantic import Field
from ch02_setup import call_with_envelope, Confidence

SERVICE_DESCRIPTIONS = {
    "catalog":  "browse products, prices, availability, stock",
    "checkout": "add to cart, place an order, apply discount codes",
    "orders":   "view past orders, refunds, returns, shipping status",
    "payments": "billing, charges, refunds, double-charge questions",
}

class RouteDecision(Confidence):
    service: str = Field(description="One of: catalog, checkout, orders, payments")

def path_based_fallback(query: str) -> RouteDecision:
    """Deterministic fallback when the LLM is unavailable or unsure."""
    q = query.lower()
    if "order" in q or "refund" in q or "return" in q:
        return RouteDecision(service="orders", confidence=1.0)
    if "cart" in q or "checkout" in q or "buy" in q:
        return RouteDecision(service="checkout", confidence=1.0)
    return RouteDecision(service="catalog", confidence=1.0)             #A

def route(user_query: str) -> RouteDecision:
    prompt = f"""Pick the SINGLE best service to handle this user request.

Available services:
{SERVICE_DESCRIPTIONS}

User request: {user_query!r}

Set confidence below 0.6 if more than one service could handle the request."""
    return call_with_envelope(
        prompt=prompt,
        schema=RouteDecision,
        fallback=lambda: path_based_fallback(user_query),
    )

if __name__ == "__main__":
    queries = [
        "show me warm jackets under $100",
        "why was I charged twice for order 1234?",
        "I want to apply discount code SUMMER20",
    ]
    for q in queries:
        d = route(q)
        print(f"{q[:48]:50} -> {d.service:10}  conf={d.confidence:.2f}")
