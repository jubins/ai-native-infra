"""
listing_2_13.py — Adaptive security: flag unusual requests for review.
Run: python listing_2_13.py
"""
from pydantic import Field
from ch02_setup import call_with_envelope, Confidence

class AnomalyResult(Confidence):
    unusual: bool
    reasons: list[str] = Field(default_factory=list)

def all_clear() -> AnomalyResult:
    return AnomalyResult(unusual=False, reasons=[], confidence=0.0)

review_queue: list[dict] = []

def flag_for_review(req: dict, reasons: list[str]):
    review_queue.append({"req": req, "reasons": reasons})

def assess_request(req: dict, baseline: dict) -> None:
    """Flag, do not block. Block decisions live in the deterministic WAF rules."""
    out = call_with_envelope(
        prompt=(f"Compare this request to the recent baseline.\n"
                f"Baseline: {baseline}\nRequest: {req}\n"
                f"Set unusual=true only if the pattern is meaningfully different."),
        schema=AnomalyResult,
        fallback=all_clear,
    )
    if out.unusual and out.confidence > 0.7:                         #A
        flag_for_review(req, out.reasons)

if __name__ == "__main__":
    baseline = {"avg_requests_per_user_per_min": 3,
                "common_user_agents": ["Chrome", "Safari", "Firefox"],
                "typical_endpoints": ["/catalog", "/checkout"]}

    requests = [
        {"user": "u_42", "rpm": 4,    "user_agent": "Chrome",   "endpoint": "/catalog"},
        {"user": "u_99", "rpm": 240,  "user_agent": "curl/7.0", "endpoint": "/admin/dump"},
    ]
    for r in requests:
        assess_request(r, baseline)

    print(f"Review queue has {len(review_queue)} item(s):")
    for item in review_queue:
        print(f"  {item['req']['user']}: {item['reasons']}")
