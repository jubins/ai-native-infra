"""
listing_2_2.py — Semantic search using embeddings.
Run: python listing_2_2.py
Requires GEMINI_API_KEY in the environment.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[3] / "appendix_a"))
import math
from ch02_setup import embed, SAMPLE_PRODUCTS

def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

def semantic_search(products: list[dict], query: str, limit: int = 5) -> list[dict]:
    """Return products ranked by semantic similarity of their description to the query."""
    q_vec = embed(query)
    scored = []
    for p in products:
        p_vec = embed(p["description"])           #A
        score = cosine_similarity(q_vec, p_vec)
        scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    return [{"score": round(s, 3), **p} for s, p in scored[:limit]]

if __name__ == "__main__":
    user_query = "warm jacket for under $100"
    results = semantic_search(SAMPLE_PRODUCTS, user_query)
    print(f"Query:   {user_query!r}")
    for r in results:
        price = r["price_cents"] / 100
        print(f"  {r['score']:.3f}  {r['name']:<24}  (${price:.2f})")
