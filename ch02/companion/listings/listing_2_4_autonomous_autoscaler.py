"""
listing_2_4.py — Autonomous autoscaler that reasons from current context.
Run: python listing_2_4.py
Requires GEMINI_API_KEY in the environment.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[3] / "appendix_a"))
from pydantic import Field
from ch02_setup import call_with_envelope, Confidence

class ScaleDecision(Confidence):
    scale_up: bool
    reason: str = Field(default="")

def static_threshold(metrics: dict) -> ScaleDecision:
    """The deterministic fallback — same logic as listing 2.3, just typed."""
    return ScaleDecision(
        scale_up=metrics["cpu_percent"] > 70,
        reason="static CPU>70% rule",
        confidence=1.0,                                       #A
    )

def should_scale_up(metrics: dict, context: dict) -> ScaleDecision:
    prompt = f"""You are a capacity planner for a web service.
Decide whether we should add a pod RIGHT NOW.

Recent metrics:
{metrics}

Recent context (last deploy, marketing events, time of day):
{context}

A 'yes' is appropriate if traffic is climbing or about to climb.
A 'no' is appropriate if CPU is high but traffic is flat (e.g. a batch job).
Set confidence below 0.6 if you are not sure."""
    return call_with_envelope(
        prompt=prompt,
        schema=ScaleDecision,
        fallback=lambda: static_threshold(metrics),           #B
    )

if __name__ == "__main__":
    quiet_morning = {"cpu_percent": 78, "rps": 12, "queue_depth": 0}
    quiet_context = {"time_of_day": "03:00 Tuesday",
                     "active_events": [],
                     "last_deploy": "8h ago"}
    flash_sale = {"cpu_percent": 65, "rps": 4500, "queue_depth": 320}
    flash_context = {"time_of_day": "12:00 Friday",
                     "active_events": ["Black Friday sale opened 4 minutes ago"],
                     "last_deploy": "2 days ago"}

    for label, m, c in [("Quiet morning", quiet_morning, quiet_context),
                        ("Flash sale opens", flash_sale, flash_context)]:
        d = should_scale_up(m, c)
        print(f"{label:20}  scale_up={d.scale_up!s:5}  conf={d.confidence:.2f}  ({d.reason})")
