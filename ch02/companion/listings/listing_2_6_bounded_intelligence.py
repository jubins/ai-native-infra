"""
listing_2_6.py — The bounded-intelligence envelope, demonstrated end-to-end.
Run: python listing_2_6.py
"""
import time
from typing import Type, Callable, TypeVar
from pydantic import BaseModel, Field, ValidationError

T = TypeVar("T", bound=BaseModel)

class Confidence(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)

def call_with_envelope(prompt: str,
                       schema: Type[T],
                       fallback: Callable[[], T],
                       _llm_call: Callable[[str], str],            #A
                       timeout_s: float = 5.0,
                       min_confidence: float = 0.6) -> T:
    """Wrap any probabilistic call in: timeout, schema, confidence floor, fallback."""
    try:
        start = time.time()
        raw = _llm_call(prompt)                                    #B
        if time.time() - start > timeout_s:
            raise TimeoutError(f"LLM took longer than {timeout_s}s")
        result = schema.model_validate_json(raw)                   #C
        if result.confidence < min_confidence:                     #D
            return fallback()
        return result
    except (TimeoutError, ValidationError, Exception):             #E
        return fallback()

# ----- Demo: four kinds of LLM behaviour, all handled by the same envelope ----
class Decision(Confidence):
    answer: str

def fallback(): return Decision(answer="FALLBACK", confidence=0.0)

def llm_good(prompt):    return '{"answer": "yes", "confidence": 0.9}'
def llm_unsure(prompt):  return '{"answer": "yes", "confidence": 0.3}'
def llm_garbage(prompt): return 'not even json'
def llm_slow(prompt):    time.sleep(0.2); return '{"answer": "yes", "confidence": 0.9}'

if __name__ == "__main__":
    cases = [
        ("Healthy LLM, high confidence", llm_good,    {}),
        ("Healthy LLM, low confidence",  llm_unsure,  {}),
        ("LLM returns malformed JSON",   llm_garbage, {}),
        ("LLM exceeds timeout",          llm_slow,    {"timeout_s": 0.05}),
    ]
    for label, llm, kwargs in cases:
        result = call_with_envelope("test", Decision, fallback, _llm_call=llm, **kwargs)
        print(f"  {label:35}  -> answer={result.answer!r}  confidence={result.confidence}")
