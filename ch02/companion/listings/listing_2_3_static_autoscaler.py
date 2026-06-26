"""
listing_2_3.py — Static rule autoscaler.
Run: python listing_2_3.py
"""
def should_scale_up(metrics: dict) -> bool:
    """Pseudocode for a threshold-based autoscaler — fires the same way every time."""
    return metrics["cpu_percent"] > 70   # A

if __name__ == "__main__":
    # Same threshold whether it's 03:00 on a Tuesday or 12:00 on Black Friday.
    quiet_morning   = {"cpu_percent": 78, "rps": 12,    "time_of_day": "03:00"}
    flash_sale_open = {"cpu_percent": 65, "rps": 4500,  "time_of_day": "12:00"}

    print(f"Quiet morning   (CPU 78%, 12 rps):   scale up? {should_scale_up(quiet_morning)}")
    print(f"Flash sale opens (CPU 65%, 4500 rps): scale up? {should_scale_up(flash_sale_open)}")
    # Wrong both ways: scales pods we don't need at 3am, fails to scale before
    # a sale even though traffic is already exploding.
