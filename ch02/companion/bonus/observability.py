"""
Observability: turn an on-call question into a structured answer.
Introduced in section 2.2.3 (Table 2.4) as the AI-Native Observability pattern.
Run: python observability.py
"""
from pydantic import Field
from ch02_setup import call_with_envelope, Confidence

class OncallAnswer(Confidence):
    answer: str
    evidence: list[str] = Field(default_factory=list)

def grafana_handoff() -> OncallAnswer:
    """The fallback is the existing dashboard. We are not replacing Grafana."""
    return OncallAnswer(
        answer="Insufficient data to answer with confidence — open the checkout dashboard in Grafana.",
        evidence=[],
        confidence=0.0,
    )

def answer(question: str, telemetry: dict) -> OncallAnswer:
    prompt = f"""You are an SRE assistant. Answer the on-call question using ONLY
the telemetry summary below. Cite specific numbers as evidence. If the data
does not support a confident answer, say so and lower your confidence.

Question: {question}

Telemetry:
{telemetry}"""
    return call_with_envelope(
        prompt=prompt,
        schema=OncallAnswer,
        fallback=grafana_handoff,
    )

if __name__ == "__main__":
    telemetry = {
        "checkout_p95_latency_ms_last_15min": 1840,
        "checkout_p95_latency_ms_baseline":   420,
        "downstream_payments_error_rate":     "12.4%",
        "downstream_payments_error_rate_24h": "0.3%",
        "deploys_last_2h": [
            {"service": "payments", "version": "v2.41.0", "ts": "14:35"},
        ],
    }
    a = answer("Why is checkout slow right now?", telemetry)
    print(f"Answer:     {a.answer}")
    print(f"Evidence:   {a.evidence}")
    print(f"Confidence: {a.confidence}")
