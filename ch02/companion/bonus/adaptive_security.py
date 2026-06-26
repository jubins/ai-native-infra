"""
Adaptive security: flag requests that deviate from a known-good baseline.
Introduced in section 2.2.3 (Table 2.4) as the Adaptive Security pattern.
Run: python adaptive_security.py
"""

import time
import argparse
import json
from pydantic import Field

# ---------------------------------------------------------------------------
# In the companion repo, ch02_setup.py provides call_with_envelope and
# Confidence.  Import them if available; otherwise define minimal stubs so
# the file runs standalone with --simulate.
# ---------------------------------------------------------------------------
try:
    from ch02_setup import call_with_envelope, Confidence
except ImportError:
    from pydantic import BaseModel

    class Confidence(BaseModel):
        confidence: float = Field(ge=0.0, le=1.0)

    def call_with_envelope(prompt, schema, fallback,
                           timeout_s=5.0, min_confidence=0.6):
        """Stub: always uses the fallback (no real LLM call)."""
        return fallback()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class ScaleForecast(Confidence):                  # A
    target_pods: int
    reason: str = ""


# ---------------------------------------------------------------------------
# Deterministic fallback
# ---------------------------------------------------------------------------

def static_forecast(metrics):                     # B
    pods = 10 if metrics["cpu_percent"] > 70 else 5
    return ScaleForecast(
        target_pods=pods,
        confidence=1.0,
        reason="static CPU>70% rule",
    )


# ---------------------------------------------------------------------------
# Slow loop  (control plane — runs every ~5 minutes)
# ---------------------------------------------------------------------------

def slow_loop(metrics, context, cache, simulate=False): # C
    if simulate:
        # Return a hand-crafted forecast so the demo runs without an API key.
        forecast = _simulated_forecast(metrics, context)
    else:
        prompt = f"""You are a capacity planner for a web service.
Forecast the number of pods the catalog service will need
over the next 30 minutes.

Current metrics : {json.dumps(metrics, indent=2)}
Current context : {json.dumps(context, indent=2)}

Reply with a target_pods count and a brief reason.
Set confidence below 0.6 if you are unsure."""

        forecast = call_with_envelope(
            prompt=prompt,
            schema=ScaleForecast,
            fallback=lambda: static_forecast(metrics),
        )

    cache["catalog"] = {                          # D
        "forecast": forecast,
        "ts": time.time(),
    }
    return forecast


def _simulated_forecast(metrics, context):
    """
    Simulates the two scenarios from the chapter so the listing
    can be demonstrated without a live API key.
    """
    if context.get("event") == "flash_sale":
        return ScaleForecast(
            target_pods=24,
            confidence=0.91,
            reason=(
                "Flash sale opened 2 minutes ago; rps has tripled to 4,500. "
                "CPU (65 %) is not yet saturated because requests are queuing. "
                "Scale to 24 pods now to absorb the wave before latency degrades."
            ),
        )
    if context.get("job") == "nightly_batch":
        return ScaleForecast(
            target_pods=5,
            confidence=0.87,
            reason=(
                "CPU (78 %) is elevated by a single-threaded batch job, not by "
                "request concurrency. Adding pods will not help. Hold at 5."
            ),
        )
    return static_forecast(metrics)


# ---------------------------------------------------------------------------
# Fast loop  (data plane — runs every few seconds)
# ---------------------------------------------------------------------------

FORECAST_TTL_SECONDS = 300   # treat a forecast as stale after 5 minutes

def fast_loop(metrics, cache):                    # E
    entry = cache.get("catalog")
    if entry and (time.time() - entry["ts"]) < FORECAST_TTL_SECONDS:
        return entry["forecast"]                  # F
    return static_forecast(metrics)               # G


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _print_forecast(label, forecast):
    print(f"\n  {label}")
    print(f"    target_pods : {forecast.target_pods}")
    print(f"    confidence  : {forecast.confidence:.2f}")
    print(f"    reason      : {forecast.reason}")


def main(simulate):
    cache = {}

    # -----------------------------------------------------------------------
    # Scenario 1: flash sale opens — CPU not yet spiked but rps has tripled
    # -----------------------------------------------------------------------
    print("=" * 62)
    print("Scenario 1 — flash sale opens (CPU 65 %, rps 4,500)")
    print("=" * 62)

    metrics_sale  = {"cpu_percent": 65, "rps": 4500, "queue_depth": 312}
    context_sale  = {
        "time_of_day": "12:02",
        "event": "flash_sale",
        "event_started_minutes_ago": 2,
        "recent_deploy": False,
    }

    print("\n[slow loop] calling model …")
    forecast = slow_loop(metrics_sale, context_sale, cache, simulate=simulate)
    _print_forecast("slow loop wrote:", forecast)

    print("\n[fast loop] reading cache …")
    decision = fast_loop(metrics_sale, cache)
    _print_forecast("fast loop read:", decision)

    # -----------------------------------------------------------------------
    # Scenario 2: nightly batch job — CPU high but no user traffic
    # -----------------------------------------------------------------------
    print("\n" + "=" * 62)
    print("Scenario 2 — nightly batch job (CPU 78 %, rps 12)")
    print("=" * 62)

    cache.clear()   # fresh cache for the second scenario

    metrics_batch = {"cpu_percent": 78, "rps": 12,  "queue_depth": 0}
    context_batch = {
        "time_of_day": "03:00",
        "job": "nightly_batch",
        "event": None,
        "recent_deploy": False,
    }

    print("\n[slow loop] calling model …")
    forecast = slow_loop(metrics_batch, context_batch, cache, simulate=simulate)
    _print_forecast("slow loop wrote:", forecast)

    print("\n[fast loop] reading cache …")
    decision = fast_loop(metrics_batch, cache)
    _print_forecast("fast loop read:", decision)

    # -----------------------------------------------------------------------
    # Scenario 3: stale / missing forecast — fast loop falls back
    # -----------------------------------------------------------------------
    print("\n" + "=" * 62)
    print("Scenario 3 — stale forecast (fast loop fallback)")
    print("=" * 62)

    cache.clear()   # empty cache simulates a missing or expired forecast

    metrics_now = {"cpu_percent": 58, "rps": 1800, "queue_depth": 4}
    print("\n[fast loop] no valid forecast in cache …")
    decision = fast_loop(metrics_now, cache)
    _print_forecast("fast loop fallback:", decision)
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="listing_2_12a — predictive scaling demo")
    parser.add_argument(
        "--simulate",
        action="store_true",
        default=False,
        help="Use simulated model responses (no API key required)",
    )
    args = parser.parse_args()
    main(simulate=args.simulate)
