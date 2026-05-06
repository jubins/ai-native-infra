"""
Listing 1.3 — Naive health checker (no guardrails).

This is the deliberately-flawed first version. It works, but it
violates every governance principle: unstructured output, no fallback,
no audit logging, no scope limits.

The production-shaped version is in listing_1_4_to_1_8_health_checker.py.
"""
import os

import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-3-flash-preview")


def check_health(log_line: str) -> str:
    """Send a log line to Gemini and return its analysis."""
    response = model.generate_content(                                 # A
        f"Analyze this log entry: {log_line}"
    )
    return response.text                                               # B


if __name__ == "__main__":
    log = "ERROR: Connection refused to postgres:5432 after 3 retries"
    print(check_health(log))

# A Sends raw, unprompted log text — no schema, no constraints on output format.
# B Returns unstructured prose — useful for humans, but impossible for machines
#   to act on reliably.
