"""
listing_2_9.py — Hybrid storage: exact match and semantic match against the same data.
Run: python listing_2_9.py

Demonstrates the two access paths in plain Python, without needing pgvector.
The production version uses Postgres `WHERE id = $1` for exact and
`ORDER BY description_vec <-> $1::vector` for semantic.
"""
import math
from ch02_setup import embed, SAMPLE_PRODUCTS

def exact_match(products: list[dict], product_id: str) -> dict | None:
    """Deterministic, sub-millisecond lookup by id."""
    for p in products:
        if p["id"] == product_id:                                #A
            return p
    return None

def semantic_match(products: list[dict], query: str, k: int = 3) -> list[dict]:
    """Probabilistic, ~10ms ranking by meaning."""
    qv = embed(query)
    def cosine(a, b):
        dot = sum(x*y for x, y in zip(a, b))
        return dot / (math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b)))
    scored = [(cosine(qv, embed(p["description"])), p) for p in products]
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:k]]

if __name__ == "__main__":
    print("Exact match (id='p_002'):")
    p = exact_match(SAMPLE_PRODUCTS, "p_002")
    print(f"  {p['name']}")

    print("\nSemantic match ('cold weather coat'):")
    for r in semantic_match(SAMPLE_PRODUCTS, "cold weather coat"):
        print(f"  {r['name']}")
