"""
Intelligent events: priority and routing inferred from event content.
Introduced in section 2.2.3 (Table 2.4) as the Intelligent Events pattern.
Run: python intelligent_events.py
"""
from pydantic import Field
from ch02_setup import call_with_envelope, Confidence

VALID_PRIORITIES = {"low", "normal", "high"}
VALID_SUBSCRIBERS = {"fulfillment", "retention", "fraud", "all"}

class EventClass(Confidence):
    priority: str = Field(description="One of: low, normal, high")
    subscribers: list[str] = Field(description="Subset of: fulfillment, retention, fraud, all")
    reason: str = ""

def default_classification() -> EventClass:
    """Deterministic fallback: every event goes to everyone at normal priority."""
    return EventClass(priority="normal", subscribers=["all"],
                      reason="default", confidence=1.0)

def classify_event(evt: dict) -> EventClass:
    prompt = f"""Classify this order event for downstream routing.

Event: {evt}

Priority high: VIP customers, very large orders, suspected fraud, repeated cancellations.
Priority low: small routine orders that any subscriber can pick up later.
Priority normal: everything else.

Subscribers — pick only those that should care about this specific event."""
    result = call_with_envelope(
        prompt=prompt,
        schema=EventClass,
        fallback=default_classification,
    )
    # Bounded intelligence: enforce the allowlist even after the LLM has spoken.
    if result.priority not in VALID_PRIORITIES:                           #A
        return default_classification()
    if not set(result.subscribers).issubset(VALID_SUBSCRIBERS):
        return default_classification()
    return result

if __name__ == "__main__":
    events = [
        {"type": "order.completed", "amount_cents": 1200, "customer_tier": "standard"},
        {"type": "order.cancelled", "amount_cents": 489000, "customer_tier": "vip",
         "reason": "customer changed mind", "previous_cancellations_30d": 3},
    ]
    for e in events:
        c = classify_event(e)
        print(f"{e['type']:20} priority={c.priority:6} subs={c.subscribers}")
