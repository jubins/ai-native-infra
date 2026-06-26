"""
Adaptive APIs: translate a v1 payload into v2 at the edge.
Introduced in section 2.2.3 (Table 2.4) as the Adaptive APIs pattern.
Run: python adaptive_api.py
"""
from pydantic import BaseModel, Field
from ch02_setup import call_with_envelope, Confidence

# V2 is the canonical schema. V1 had different field names.
class V2Item(BaseModel):
    sku: str
    qty: int

class V2Payload(Confidence):
    customer_id: str
    items: list[V2Item]
    currency: str
    total_cents: int

def legacy_translator(v1: dict) -> V2Payload:
    """Hand-written deterministic mapping — exists for the cases AI cannot handle."""
    return V2Payload(
        customer_id=str(v1.get("cust") or v1.get("customer") or v1.get("user_id", "unknown")),
        items=[V2Item(sku=str(it.get("product") or it.get("sku")),
                      qty=int(it.get("count") or it.get("qty") or 1))
               for it in v1.get("line_items") or v1.get("items") or []],
        currency=v1.get("ccy") or v1.get("currency") or "USD",
        total_cents=int(v1.get("total_cents") or round(float(v1.get("total", 0)) * 100)),
        confidence=1.0,
    )

def adapt(v1_payload: dict) -> V2Payload:
    prompt = f"""Translate this incoming payload into the V2 schema.
Allowed source fields: {list(v1_payload.keys())}
Source payload: {v1_payload}

Map fields by meaning. Convert dollar amounts to cents. Do not invent values."""
    return call_with_envelope(
        prompt=prompt,
        schema=V2Payload,
        fallback=lambda: legacy_translator(v1_payload),                 #A
    )

if __name__ == "__main__":
    legacy_payload = {
        "cust": "u_42",
        "line_items": [{"product": "p_001", "count": 2},
                       {"product": "p_003", "count": 1}],
        "ccy": "USD",
        "total": 24.70,        # dollars, not cents
    }
    v2 = adapt(legacy_payload)
    print(f"customer_id: {v2.customer_id}")
    print(f"items:       {[(i.sku, i.qty) for i in v2.items]}")
    print(f"total_cents: {v2.total_cents}")
    print(f"confidence:  {v2.confidence}")
