"""
Listings 1.4 – 1.9 — Production-shaped intelligent health checker.

Implements all four governance principles in a single working module:

    Principle 1 — Deterministic fallback (regex severity classifier)
    Principle 2 — Inspectable & reversible (audit log per assessment)
    Principle 3 — Explicit scope limits (advisory output only)
    Principle 4 — Human override (no autonomous remediation)

Run:
    export GEMINI_API_KEY="your-key"
    python listing_1_4_to_1_9_health_checker.py
"""

# ---- Listing 1.4: data model ---------------------------------------------
import google.generativeai as genai
import json
import logging
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health_checker")


class Severity(str, Enum):                                             # A
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthAssessment:
    severity: Severity
    component: str
    root_cause: str
    suggested_action: str
    confidence: float
    source: str             # "ai" or "fallback"                       # B
    timestamp: str = ""

    def __post_init__(self):                                           # C
        if not self.timestamp:
            self.timestamp = datetime.now(
                timezone.utc).isoformat()

# A The enum constrains severity to exactly four values; both AI and fallback
#   paths must use these.
# B "ai" or "fallback" — every assessment records how it was produced,
#   supporting auditability (Principle 2).
# C Auto-populates a UTC timestamp so every assessment is temporally traceable.


# ---- Listing 1.5: class setup and the analyze entry point ----------------
class IntelligentHealthChecker:
    """AI-native health checker with governance guardrails."""

    LLM_TIMEOUT = 5.0                                                  # A
    ANALYSIS_PROMPT = """Analyze this log entry and return
JSON with exactly these fields:
- severity: one of "low","medium","high","critical"
- component: the service or component name
- root_cause: one-sentence root cause summary
- suggested_action: one-sentence remediation
- confidence: float from 0.0 to 1.0

Log entry: {log_line}
Return only valid JSON."""                                             # B

    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel(
            "gemini-3-flash-preview")

    def analyze(self, log_line: str) -> HealthAssessment:
        """Main entry point. Always returns."""
        try:
            return self._ai_analyze(log_line)                          # C
        except Exception as e:                                         # D
            logger.warning(
                f"AI failed ({e}), using fallback")
            return self._fallback_analyze(log_line)

    # A Hard ceiling — if the LLM takes longer than 5 seconds, we treat it as
    #   a failure.
    # B Prompt constrains LLM output to a specific JSON schema; structured
    #   output is critical for machine consumption.
    # C Happy path: attempt AI-powered analysis first.
    # D Principle 1 in action — any AI failure (timeout, malformed JSON,
    #   API error) falls through to the deterministic path. The caller never
    #   sees an exception.

    # ---- Listing 1.6: AI analysis path -----------------------------------
    def _ai_analyze(self, log_line: str) -> HealthAssessment:
        start = time.time()
        prompt = self.ANALYSIS_PROMPT.format(
            log_line=log_line)
        response = self.model.generate_content(prompt)
        elapsed = time.time() - start

        if elapsed > self.LLM_TIMEOUT:                                 # A
            raise TimeoutError(f"LLM took {elapsed:.1f}s")

        text = response.text.strip()
        if text.startswith("```"):                                     # B
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        data = json.loads(text)                                        # C

        assessment = HealthAssessment(
            severity=Severity(data["severity"]),
            component=data["component"],
            root_cause=data["root_cause"],
            suggested_action=data["suggested_action"],
            confidence=float(data["confidence"]),
            source="ai")

        self._audit_log(                                               # D
            log_line, prompt, text, assessment)
        return assessment

    # A Post-hoc timeout — the SDK lacks a native timeout, so we enforce our
    #   own SLA after the call completes.
    # B Gemini occasionally wraps JSON in Markdown fences; strip them
    #   defensively.
    # C Raises ValueError if the response is not valid JSON — caught by
    #   analyze() and rerouted to fallback.
    # D Every AI decision is audit-logged before returning (Principle 2).

    # ---- Listing 1.7: regex-based fallback (Principle 1) -----------------
    def _fallback_analyze(self, log_line: str) -> HealthAssessment:
        severity = Severity.MEDIUM                                     # A
        if re.search(r"CRITICAL|FATAL|OOM|panic",
                     log_line, re.IGNORECASE):
            severity = Severity.CRITICAL                               # B
        elif re.search(r"ERROR|Exception|refused",
                       log_line, re.IGNORECASE):
            severity = Severity.HIGH                                   # B
        elif re.search(r"WARN|timeout|slow",
                       log_line, re.IGNORECASE):
            severity = Severity.MEDIUM                                 # B

        comp = re.search(r"(\w+Service|\w+Worker)",
                         log_line)
        component = comp.group(1) if comp else "unknown"               # C

        return HealthAssessment(
            severity=severity,
            component=component,
            root_cause="Determined by pattern matching",
            suggested_action="Review logs manually",                   # D
            confidence=0.3,
            source="fallback")

    # A Default to MEDIUM when no keyword matches — a safe middle ground.
    # B Keyword-based severity: simple but reliable when the LLM is unavailable.
    # C Extracts the service name by convention (e.g., PaymentService,
    #   OrderWorker).
    # D Low confidence signals to downstream consumers that the assessment
    #   requires human review.

    # ---- Listing 1.8: audit logging (Principle 2) ------------------------
    def _audit_log(self, log_line, prompt, resp, assessment):
        logger.info(json.dumps({
            "event": "health_check_analysis",                          # A
            "input": log_line[:200],                                   # B
            "assessment": asdict(assessment),
            "llm_response_length": len(resp),                          # C
            "timestamp": assessment.timestamp,
        }))

    # A Structured event name for log aggregation and querying.
    # B Truncate input to 200 chars — avoids bloating logs while preserving
    #   enough context for debugging.
    # C Log response length rather than the full response — saves storage
    #   while remaining useful for detecting anomalies.


# ---- Listing 1.9: testing the health checker -----------------------------
if __name__ == "__main__":
    checker = IntelligentHealthChecker()
    test_logs = [
        "2026-03-14 02:13:45 ERROR PaymentService - Timeout"
        " waiting for stripe-api.internal:443."
        " Retry attempt 3/3 failed.",                                  # A
        "2026-03-14 09:00:01 INFO HealthCheck"
        " - All systems nominal."
        " Response time: 45ms",                                        # B
        "2026-03-14 14:22:33 CRITICAL OrderWorker"
        " - OOMKilled. Container exceeded 2Gi memory limit."
        " Last processed: order_id=9f3b2a",                            # C
    ]

    for log in test_logs:
        print(f"\n{'=' * 60}")
        print(f"LOG: {log[:80]}...")
        print(f"{'=' * 60}")
        assessment = checker.analyze(log)                              # D
        print(f"  Severity:   {assessment.severity.value}")
        print(f"  Component:  {assessment.component}")
        print(f"  Cause:      {assessment.root_cause}")
        print(f"  Action:     {assessment.suggested_action}")
        print(f"  Confidence: {assessment.confidence}")
        print(f"  Source:     {assessment.source}")                    # E

# A External-dependency failure — tests whether the AI identifies Stripe as
#   the root cause, not PaymentService.
# B Healthy log — tests whether the AI correctly classifies low severity and
#   avoids false alarms.
# C Resource exhaustion — tests whether the AI catches the OOM kill and
#   recommends a memory-limit increase.
# D analyze() always returns and never throws — the caller does not need to
#   know which path produced the result.
# E The source field reveals whether AI or the fallback handled each log line.
