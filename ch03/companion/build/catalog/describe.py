"""
Listing 3.17: catalog/describe.py

AI-generated product description with a static-template fallback.
Called by the POST /catalog/products/{product_id}/describe route in main.py.

The function has two paths:
  - LLM path: Gemini responds with a usable description  → strategy: llm_generated
  - Fallback path: any failure (network, quota, short response) → strategy: static_template

The broad except is deliberate: every failure mode produces a usable description
and fallback_used: true rather than surfacing an error to the caller.
"""
import os

import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_model = genai.GenerativeModel("gemini-1.5-flash")

_STATIC_TEMPLATES = {
    "professional": "{name}. Priced at ${price}.",
    "casual":       "Check out {name} — only ${price}!",
}

_PROMPTS = {
    "professional": (
        "Write a two-sentence professional product description for an "
        "e-commerce detail page. Product: {name}. Price: ${price}. "
        "Category: {category}. Reply with the description only."
    ),
    "casual": (
        "Write a two-sentence casual, friendly product description for "
        "a social recommendation surface. Product: {name}. Price: ${price}. "
        "Category: {category}. Reply with the description only."
    ),
}


async def generate_description(product: dict, tone: str) -> dict:
    name     = product["name"]
    price    = product["price_cents"] / 100
    category = product.get("category", "general")

    try:
        prompt   = _PROMPTS[tone].format(
                       name=name, price=f"{price:.2f}", category=category)
        response = _model.generate_content(prompt)           #A
        text     = response.text.strip()

        if not text or len(text) < 20:                       #B
            raise ValueError("Response too short to trust")

        return {
            "description": text,
            "decision": {
                "strategy":          "llm_generated",
                "confidence":        0.91,                   #C
                "fallback_used":     False,
                "fallback_strategy": "static_template",
            }
        }

    except Exception:                                        #D
        fallback = _STATIC_TEMPLATES[tone].format(
                       name=name, price=f"{price:.2f}")
        return {
            "description": fallback,
            "decision": {
                "strategy":          "static_template",
                "confidence":        None,
                "fallback_used":     True,
                "fallback_strategy": "static_template",
            }
        }

#A A single generate_content call. The model, prompt shape, and API key are
#  module-level — one import, no per-request setup.
#B A response shorter than 20 characters is not a usable description. Treating
#  it as a failure triggers the fallback rather than returning unusable output.
#C Gemini does not return a confidence score natively. 0.91 is a fixed signal
#  meaning "the LLM responded and passed the length check." A production system
#  would derive this from output length, response latency, or a secondary call.
#D Network errors, API quota errors, and parse failures all produce the same
#  outcome: a usable static description and fallback_used: true.
