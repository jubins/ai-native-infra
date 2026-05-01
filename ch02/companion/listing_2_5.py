"""
listing_2_5.py — Anti-pattern: a ranker that learns from its own decisions.
Run: python listing_2_5.py

Demonstrates the failure mode by simulating five days of operation, where each
day's "popularity" comes from yesterday's ranking rather than from real signals.
"""
from ch02_setup import SAMPLE_PRODUCTS

# Start with equal popularity for every product.
popularity = {p["id"]: 1.0 for p in SAMPLE_PRODUCTS}

def update_popularity(ranked_products: list[dict]):
    """Treat the system's own ranking as evidence of what is popular. (THE BUG.)"""
    for rank, p in enumerate(ranked_products):
        weight = 1.0 / (rank + 1)
        popularity[p["id"]] += weight                        #A

def rank(products: list[dict]) -> list[dict]:
    """Rank by popularity — which we are about to overwrite from our own output."""
    return sorted(products, key=lambda p: -popularity[p["id"]])  #B

if __name__ == "__main__":
    # Tiny tiebreaker so day 1's order is deterministic.
    popularity["p_001"] += 0.001

    print(f"{'Day':>3}  {'Top 3':<60}  popularity[p_001]")
    print("-" * 88)
    for day in range(1, 6):
        ranked = rank(SAMPLE_PRODUCTS)
        update_popularity(ranked)                           #C
        top3 = ", ".join(p["name"] for p in ranked[:3])
        print(f"{day:>3}  {top3:<60}  {popularity['p_001']:.3f}")

    print("\nThe system has 'learned' that p_001 is the most popular product —")
    print("not because users prefer it, but because it ranked first on day 1.")
