# Chapter 1 — Companion code

Companion folder for **Chapter 1 — The AI-Native Paradigm Shift**.

## Setup

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key-here"
```

An API key can be obtained for free from
[Google AI Studio](https://aistudio.google.com). The free tier comfortably
covers every exercise in chapters 1 – 10.

For a fully frozen install (e.g. CI, or to reproduce exactly the versions the
book was written against), use the lock file instead:

```bash
pip install -r requirements-lock.txt
```

Then run any listing directly:

```bash
python listings/listing_1_1_structured_llm_call.py
```

## Structure

`listing_1_4_to_1_9_health_checker.py` is shared scaffolding: it consolidates
Listings 1.4 – 1.9 (the production-shaped health checker) into one runnable
module so readers can execute the full example end to end without copy-paste
assembly. The components inside it are:

- `Severity` — enum with the four severity levels every assessment must use.
- `HealthAssessment` — dataclass that serves as the contract between the AI
  path and the deterministic fallback. The `source` field records which path
  produced the assessment.
- `IntelligentHealthChecker` — class implementing all four governance
  principles: deterministic fallback, audit logging, scope limits, and human
  override.
- `IntelligentHealthChecker.analyze()` — the bounded-intelligence entry point
  used by every example in the chapter. Always returns; never throws.

## Listings

The mapping from listings in the chapter to files in this folder:

| In the chapter | File                                       | What it does                                               |
| -------------- | ------------------------------------------ | ---------------------------------------------------------- |
| Listing 1.1    | `listing_1_1_structured_llm_call.py`       | Structured LLM call with Gemini; unstructured log → JSON.  |
| Listing 1.2    | `listing_1_2_setup.sh`                     | One-time project setup (venv + dependencies).              |
| Listing 1.3    | `listing_1_3_naive_health_checker.py`      | Naive health checker; deliberately violates governance.    |
| Listing 1.4    | `listing_1_4_to_1_9_health_checker.py`     | Data model: `Severity` enum and `HealthAssessment`.        |
| Listing 1.5    | `listing_1_4_to_1_9_health_checker.py`     | Class setup and the `analyze()` entry point.               |
| Listing 1.6    | `listing_1_4_to_1_9_health_checker.py`     | The AI analysis path with timeout enforcement.             |
| Listing 1.7    | `listing_1_4_to_1_9_health_checker.py`     | Regex-based deterministic fallback (Principle 1).          |
| Listing 1.8    | `listing_1_4_to_1_9_health_checker.py`     | Audit logging every AI decision (Principle 2).             |
| Listing 1.9    | `listing_1_4_to_1_9_health_checker.py`     | Test harness exercising three real-world log scenarios.    |

## Listings that need an API key

Listings that call Gemini require `GEMINI_API_KEY`. The naive demo and the
setup script run without one:

- **No key needed:** `listing_1_2_setup.sh`, `listing_1_3_naive_health_checker.py` *(will fail at the LLM call but compiles and imports cleanly)*
- **Key required:** `listing_1_1_structured_llm_call.py`, `listing_1_4_to_1_9_health_checker.py`

If the LLM call fails for any reason (no key, network, rate limit, timeout,
malformed response), the envelope inside `IntelligentHealthChecker.analyze()`
falls back to the deterministic regex path, and the script still produces
output. This is the bounded-intelligence principle in action.

## Cost note

Running `listing_1_4_to_1_9_health_checker.py` once issues at most three
Gemini Flash calls (≈ $0.000004 total at early-2026 prices). At one hundred
thousand analyses per day — a sizeable operation — the monthly cost is
approximately $12.
