#!/usr/bin/env bash
# ci_smoke.sh — asserting smoke tests for CI (no API key required).
# Runs the same seven checks as listing_3_21_smoke_tests.sh but exits
# non-zero on any failure so GitHub Actions marks the job as failed.
#
# Test 6 (AI description) is verified on the fallback path only:
# without GEMINI_API_KEY the endpoint returns static_template, which
# is correct behaviour and still confirms the route is wired up.
set -euo pipefail

CATALOG_URL="${CATALOG_URL:-http://localhost:8080}"
ORDERS_URL="${ORDERS_URL:-http://localhost:8081}"
PASS=0
FAIL=0

green() { echo -e "\033[32m✓  $*\033[0m"; }
red()   { echo -e "\033[31m✗  $*\033[0m"; }
hr()    { printf '\n%s\n' "------------------------------------------------------------"; }

pass() { green "$1"; PASS=$((PASS + 1)); }
fail() { red   "$1"; FAIL=$((FAIL + 1)); }
get()  { curl -sf "$1" || echo "CURL_FAILED"; }
http_status() { curl -s -o /dev/null -w "%{http_code}" "$1"; }

# 1. OpenAPI discovery
hr
body=$(get "${CATALOG_URL}/openapi.json")
echo "$body" | grep -q "/catalog/search" \
    && pass "[1] OpenAPI discovery — /catalog/search present in spec" \
    || fail "[1] OpenAPI discovery — spec missing expected paths"

# 2. Search returns confidence-carrying decision block
hr
body=$(get "${CATALOG_URL}/catalog/search?q=jacket")
echo "$body" | grep -q '"fallback_used"' \
    && pass "[2] Search response carries decision block" \
    || fail "[2] Search response missing decision block"

# 3. Empty query triggers 422 validation envelope
hr
status=$(http_status "${CATALOG_URL}/catalog/search?q=")
[ "$status" = "422" ] \
    && pass "[3] Empty query returns HTTP 422" \
    || fail "[3] Empty query returned HTTP $status (expected 422)"

# 4. Missing product returns structured 404
hr
body=$(get "${CATALOG_URL}/catalog/products/p_999")
echo "$body" | grep -q "PRODUCT_NOT_FOUND" \
    && pass "[4] Unknown product returns PRODUCT_NOT_FOUND envelope" \
    || fail "[4] Unknown product returned unexpected body: $body"

# 5. Idempotency replay
hr
KEY=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)
PAYLOAD='{"customer_id":"cus_ci","items":[{"sku":"p_001","qty":1}]}'
curl -sf -X POST "${ORDERS_URL}/orders" \
    -H "Idempotency-Key: $KEY" \
    -H 'Content-Type: application/json' \
    -d "$PAYLOAD" > /dev/null  # first write

REPLAY=$(curl -si -X POST "${ORDERS_URL}/orders" \
    -H "Idempotency-Key: $KEY" \
    -H 'Content-Type: application/json' \
    -d "$PAYLOAD" || echo "")  # second write — expect replay header
echo "$REPLAY" | grep -qi "idempotent-replay: true" \
    && pass "[5] Idempotency replay header present on second request" \
    || fail "[5] Idempotency replay header missing"

# 6. AI description endpoint responds on the fallback path (no API key)
hr
body=$(curl -sf -X POST "${CATALOG_URL}/catalog/products/p_001/describe" \
    -H 'Content-Type: application/json' \
    -d '{"tone":"professional"}' || echo "CURL_FAILED")
echo "$body" | grep -q '"description"' && echo "$body" | grep -q '"decision"' \
    && pass "[6] AI description — description + decision block present (fallback path)" \
    || fail "[6] AI description — unexpected response: $body"

# 7. Describe route on unknown product returns structured 404
hr
body=$(curl -sf -X POST "${CATALOG_URL}/catalog/products/p_999/describe" \
    -H 'Content-Type: application/json' || echo "CURL_FAILED")
echo "$body" | grep -q "PRODUCT_NOT_FOUND" \
    && pass "[7] Describe on unknown product returns PRODUCT_NOT_FOUND envelope" \
    || fail "[7] Describe 404 — unexpected response: $body"

# ── Summary ──────────────────────────────────────────────────────────────────
hr
echo "  passed: $PASS"
echo "  failed: $FAIL"

if [ "$FAIL" -eq 0 ]; then
    echo -e "\n\033[32mAll $PASS checks passed.\033[0m"
    exit 0
else
    echo -e "\n\033[31m$FAIL check(s) failed.\033[0m"
    exit 1
fi
