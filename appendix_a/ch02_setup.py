"""
ch02_setup.py — shared scaffolding for every listing in chapter 2.
Reader runs this once; every later listing imports from it.

Requires:
    pip install google-genai pydantic asyncpg fastapi httpx
    export GEMINI_API_KEY=...
"""
import os
import json
import time
from typing import Type, Callable, TypeVar
from pydantic import BaseModel, Field, ValidationError

# ---- Gemini client (lazy-init so listings that don't need AI still run) ----
_client = None
def llm_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client

MODEL = "gemini-2.5-flash"
EMBED_MODEL = "gemini-embedding-001"

# ---- The bounded-intelligence envelope -----------------------------------
T = TypeVar("T", bound=BaseModel)

class Confidence(BaseModel):
    """Mixin: every structured response must carry a confidence score."""
    confidence: float = Field(ge=0.0, le=1.0)

def call_llm_structured(prompt: str, schema: Type[T], timeout_s: float = 5.0) -> T:
    """Call Gemini with native structured output. Returns a parsed schema or raises."""
    from google.genai import types
    start = time.time()
    response = llm_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.0,
        ),
    )
    if time.time() - start > timeout_s:
        raise TimeoutError(f"LLM took longer than {timeout_s}s")
    return response.parsed   # already a typed pydantic instance

def call_with_envelope(prompt: str,
                       schema: Type[T],
                       fallback: Callable[[], T],
                       _llm_call: Callable[..., T] | None = None,  #A
                       timeout_s: float = 5.0,
                       min_confidence: float = 0.6) -> T:
    """The pattern every AI-native component in this book follows."""
    llm = _llm_call or (lambda p: call_llm_structured(p, schema, timeout_s=timeout_s))
    try:
        result = llm(prompt)
        if hasattr(result, "confidence") and result.confidence < min_confidence:
            return fallback()
        return result
    except (TimeoutError, ValidationError, Exception):
        return fallback()
#A Injected so the same envelope works with any model and so callers can test it without a real API key.

def embed(text: str) -> list[float]:
    """Turn any text into a 768-dim vector that captures its meaning."""
    from google.genai import types
    r = llm_client().models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return r.embeddings[0].values

# ---- A tiny in-memory product catalog used by several listings ------------
SAMPLE_PRODUCTS = [
    {"id": "p_001", "name": "Merino Wool Jacket",  "price_cents":  8900,
     "description": "Warm mid-weight winter jacket, breathable merino wool"},
    {"id": "p_002", "name": "Down Puffer Coat",   "price_cents": 12900,
     "description": "Heavy down-filled coat for cold weather, hooded"},
    {"id": "p_003", "name": "Rain Shell",          "price_cents":  6900,
     "description": "Lightweight waterproof jacket, packs into its own pocket"},
    {"id": "p_004", "name": "Summer Linen Shirt",  "price_cents":  3900,
     "description": "Breathable linen shirt for hot weather"},
    {"id": "p_005", "name": "Fleece Pullover",     "price_cents":  5900,
     "description": "Soft warm fleece, mid-layer for cold days"},
]

if __name__ == "__main__":
    # Smoke test
    print("Setup loaded. Running a smoke test of the envelope...")

    class Demo(Confidence):
        answer: str

    def fb(): return Demo(answer="fallback", confidence=0.0)

    out = call_with_envelope(
        prompt="Return JSON with answer='hello' and confidence=0.95",
        schema=Demo,
        fallback=fb,
    )
    print(f"  envelope returned: {out}")
