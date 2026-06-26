"""
listing_2_1.py — Traditional search using string matching.
Run: python listing_2_1.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[3] / "appendix_a"))
from ch02_setup import SAMPLE_PRODUCTS

def search_products(products: list[dict], query: str, limit: int = 20) -> list[dict]:
    """Return products whose name contains the query as a case-insensitive substring."""
    q = query.lower()
    matches = [p for p in products if q in p["name"].lower()]
    return matches[:limit]

if __name__ == "__main__":
    user_query = "warm jacket for under $100"
    results = search_products(SAMPLE_PRODUCTS, user_query)
    print(f"Query:   {user_query!r}")
    print(f"Matches: {len(results)}")
    for p in results:
        print(f"  - {p['name']}  (${p['price_cents']/100:.2f})")
