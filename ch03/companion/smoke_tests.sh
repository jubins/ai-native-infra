#!/usr/bin/env bash
# Listing 3.15: smoke_tests.sh — exercising the modified catalog service.
#
# Run after `make up` (or `docker compose up -d`). Each call corresponds
# to a pattern from the chapter:
#   1. OpenAPI discovery (pattern 3)
#   2. Confidence-carrying response (pattern 6)
#   3. Validation error envelope (pattern 5, framework path)
#   4. Application-level error envelope (pattern 5, APIError path)
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"

if ! command -v jq >/dev/null 2>&1; then
    echo "warning: jq is not installed; output will not be pretty-printed." >&2
    JQ="cat"
else
    JQ="jq"
fi

hr() { printf '\n%s\n' "------------------------------------------------------------"; }

# 1. The OpenAPI document is served at /openapi.json.
hr
echo "[1] OpenAPI discovery: GET /openapi.json"
curl -s "${BASE_URL}/openapi.json" | $JQ '.paths | keys'
# => [ "/catalog/products/{product_id}", "/catalog/search" ]

# 2. A valid search returns the decision block alongside the results.
hr
echo "[2] Search with decision block: GET /catalog/search?q=jacket"
curl -s "${BASE_URL}/catalog/search?q=jacket" | $JQ
# => { "results":  [ { "id": "p_001", ..., "match_score": null } ],
#      "decision": { "strategy": "keyword_ilike", "confidence": null,
#                    "fallback_used": true, "fallback_strategy": "keyword_ilike" } }

# 3. A malformed query triggers the structured error envelope.
hr
echo "[3] Validation error envelope: GET /catalog/search?q="
curl -s -i "${BASE_URL}/catalog/search?q=" | head -20
# => HTTP/1.1 422 Unprocessable Entity
#    { "error_code": "VALIDATION_FAILED", "type": "validation_error",
#      "message": "String should have at least 1 character", "field": "q", ... }

# 4. A missing product returns the structured 404.
hr
echo "[4] Application error envelope: GET /catalog/products/p_999"
curl -s "${BASE_URL}/catalog/products/p_999" | $JQ
# => { "error_code": "PRODUCT_NOT_FOUND", "type": "validation_error",
#      "message": "No product exists with identifier p_999",
#      "field": "product_id", "retryable": false, ... }

hr
echo "All four smoke tests printed above. Inspect the output to verify."
