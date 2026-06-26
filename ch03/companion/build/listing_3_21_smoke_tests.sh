#!/usr/bin/env bash
# Listing 3.21: smoke_tests.sh — seven checks covering all pattern additions.
#
# Run after `make up` (or `docker compose up -d`). Each call corresponds
# to a pattern from the chapter:
#   1. OpenAPI discovery (Pattern 3)
#   2. Confidence-carrying search response (Pattern 6)
#   3. Validation error envelope, framework path (Pattern 5)
#   4. Application-level error envelope, APIError path (Pattern 5)
#   5. Idempotency replay on POST /orders (Pattern 7)
#   6. AI-generated description with decision block (Pattern 6 + section 3.7.3)
#   7. Error middleware on the describe route (Pattern 5 + section 3.7.2)
set -euo pipefail

CATALOG_URL="${CATALOG_URL:-http://localhost:8080}"
ORDERS_URL="${ORDERS_URL:-http://localhost:8081}"

if ! command -v jq >/dev/null 2>&1; then
    echo "warning: jq is not installed; output will not be pretty-printed." >&2
    JQ="cat"
else
    JQ="jq"
fi

hr() { printf '\n%s\n' "------------------------------------------------------------"; }

# 1. The OpenAPI document is served at /openapi.json.                          #A
hr
echo "[1] OpenAPI discovery: GET /openapi.json"
curl -s "${CATALOG_URL}/openapi.json" | $JQ '.paths | keys'
# => [ "/catalog/products/{product_id}",
#      "/catalog/products/{product_id}/describe",
#      "/catalog/search" ]

# 2. A valid search returns the decision block alongside the results.           #B
hr
echo "[2] Search with decision block: GET /catalog/search?q=jacket"
curl -s "${CATALOG_URL}/catalog/search?q=jacket" | $JQ
# => { "results":  [ { "id": "p_001", ..., "match_score": null } ],
#      "decision": { "strategy": "keyword_ilike", "confidence": null,
#                    "fallback_used": true, "fallback_strategy": "keyword_ilike" } }

# 3. A malformed query triggers the structured error envelope.                 #C
hr
echo "[3] Validation error envelope: GET /catalog/search?q="
curl -s -i "${CATALOG_URL}/catalog/search?q=" | head -20
# => HTTP/1.1 422 Unprocessable Entity
#    { "error_code": "VALIDATION_FAILED", "type": "validation_error",
#      "message": "String should have at least 1 character", "field": "q", ... }

# 4. A missing product returns the structured 404.                             #D
hr
echo "[4] Application error envelope: GET /catalog/products/p_999"
curl -s "${CATALOG_URL}/catalog/products/p_999" | $JQ
# => { "error_code": "PRODUCT_NOT_FOUND", "type": "validation_error",
#      "message": "No product exists with identifier p_999",
#      "field": "product_id", "retryable": false, ... }

# 5. A retried write replays instead of duplicating.                           #E
hr
echo "[5] Idempotency replay: POST /orders (twice, same key)"
KEY=$(uuidgen)
curl -s -X POST "${ORDERS_URL}/orders" \
  -H "Idempotency-Key: $KEY" \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"cus_17","items":[{"sku":"p_001","qty":1}]}' | $JQ .id
curl -s -i -X POST "${ORDERS_URL}/orders" \
  -H "Idempotency-Key: $KEY" \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"cus_17","items":[{"sku":"p_001","qty":1}]}' \
  | grep -i "idempotent-replay"
# => "ord_..."
# => idempotent-replay: true

# 6. AI-generated description returns a decision block with live confidence.   #F
hr
echo "[6] AI description (LLM path): POST /catalog/products/p_001/describe"
curl -s -X POST "${CATALOG_URL}/catalog/products/p_001/describe" \
  -H 'Content-Type: application/json' \
  -d '{"tone": "professional"}' | $JQ '{description, decision}'
# => { "description": "A lightweight merino wool jacket...",
#      "decision": { "strategy": "llm_generated", "confidence": 0.91,
#                    "fallback_used": false,
#                    "fallback_strategy": "static_template" } }

# 7. An unknown product_id on the describe route returns a structured 404.     #G
hr
echo "[7] Describe 404 envelope: POST /catalog/products/p_999/describe"
curl -s -X POST "${CATALOG_URL}/catalog/products/p_999/describe" \
  -H 'Content-Type: application/json' | $JQ '{error_code, type, field}'
# => { "error_code": "PRODUCT_NOT_FOUND",
#      "type": "validation_error",
#      "field": "product_id" }

hr
echo "All seven smoke tests printed above. Inspect the output to verify."

#A Confirms Pattern 3: specification discoverable at runtime from a stable path.
#B Confirms Pattern 6: every search response carries the decision block, even on the fallback path.
#C Confirms Pattern 5: framework-level validation errors rewritten into the structured envelope by the middleware.
#D Confirms Pattern 5 at the application level: APIError raised by the handler produces the same envelope shape.
#E Confirms Pattern 7: the orders service recognises the repeated key and serves the recorded response — no duplicate order in the database.
#F Confirms 3.7.3 and Pattern 6 together: a live LLM call returns a real confidence score, not null. fallback_used: false means Gemini responded.
#G Confirms 3.7.2 and 3.7.3 together: the error middleware catches the APIError raised inside the describe route and serializes it into the structured envelope.
