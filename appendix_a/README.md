# Appendix A — Shared Setup

`ch02_setup.py` is shared scaffolding used by the standalone listings in
chapter 2 (and referenced in later chapters). It provides:

- `call_with_envelope(prompt, schema, fallback, …)` — the bounded-intelligence
  envelope used by every AI-native listing.
- `embed(text)` — produces a 768-dim vector via `gemini-embedding-001`.
- `Confidence` — Pydantic mixin that every structured response inherits from.
- `SAMPLE_PRODUCTS` — a small in-memory product catalog used by the search
  and storage examples.

## Setup

Install once from the repo root before running any standalone listing:

```bash
pip install -r appendix_a/requirements.txt
export GEMINI_API_KEY="your-key-here"
```

Then run listings from the repo root so Python can find `ch02_setup`:

```bash
python ch02/companion/listings/listing_2_1_string_match.py
```

## What needs a Gemini API key

Listings that call `embed()` or `call_with_envelope()` require `GEMINI_API_KEY`.
Those that demonstrate failure modes or use static data run without one:

- No key needed: `listing_2_1_string_match.py`, `listing_2_3_static_autoscaler.py`, `listing_2_5_ranker_antipattern.py`, `listing_2_6_bounded_intelligence.py`
- Key required: `listing_2_2_semantic_search.py`, `listing_2_4_autonomous_autoscaler.py`, `listing_2_7_semantic_routing.py`, `listing_2_8_predictive_scaling.py`

If a Gemini call fails for any reason (no key, network, rate limit, malformed
response, low confidence), the envelope falls back to the deterministic path
and the script still produces output — the bounded-intelligence principle in action.
