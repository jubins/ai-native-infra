"""
listing_2_14.py — Anti-pattern: three AI calls in a chain with no checks.

Demonstrates how individual call success rates compound into pipeline failure.
Each step is "right 95% of the time" — the chain succeeds 0.95**3 = 86%.
With realistic 90% calls, the chain succeeds 73%.
"""
import random

random.seed(42)
INDIVIDUAL_SUCCESS = 0.95

def ai_classify_intent(query):
    return "lookup" if random.random() < INDIVIDUAL_SUCCESS else "GARBAGE_INTENT"

def ai_generate_sql(intent):
    if intent == "GARBAGE_INTENT" or random.random() >= INDIVIDUAL_SUCCESS:
        return "SELECT * FROM nope"
    return "SELECT id, name FROM products WHERE id = 'p_001'"

def run(sql):
    return [{"id": "p_001", "name": "Merino Wool Jacket"}] if "products" in sql else []

def ai_summarize_rows(rows):
    if not rows:
        return "No data found."   # plausible-sounding nonsense built on bad SQL
    return f"Top result: {rows[0]['name']}"

def handle(query):
    intent = ai_classify_intent(query)        #A
    sql    = ai_generate_sql(intent)          #B
    answer = ai_summarize_rows(run(sql))      #C
    return answer

if __name__ == "__main__":
    successes = sum(1 for _ in range(1000)
                    if handle("show me my favourite jacket") == "Top result: Merino Wool Jacket")
    print(f"Pipeline success rate over 1000 trials: {successes/10:.1f}%")
    print(f"Each call is right {int(INDIVIDUAL_SUCCESS*100)}% of the time;")
    print(f"the chain of three is right ~{INDIVIDUAL_SUCCESS**3*100:.0f}% of the time.")
