#!/usr/bin/env bash
# listing_2_13 — smoke_test.sh
# Brings up the skeleton and verifies the four calls from the chapter.
# Run from the build/ directory:
#
#   cd ch02/companion/build
#   bash listing_2_13_smoke_test.sh
#
# Prerequisites: Docker Desktop running, GEMINI_API_KEY exported.

set -euo pipefail

COMPOSE_DIR="$(dirname "$0")"
BASE_URL="http://localhost:8080"

# ── Listing 2.13 — bring up the skeleton and verify it ───────────────────────

cd "$COMPOSE_DIR"
docker compose -f listing_2_9_docker_compose.yml up -d --build  

# Wait ~10 seconds for Postgres to initialize, then:
echo "Waiting 12 s for Postgres to initialise…"
sleep 12

curl http://localhost:8080/health                                
# -> {"status":"ok"}

curl http://localhost:8080/catalog/products/p_001                
# -> {"id":"p_001","name":"Merino Wool Jacket",...}

curl "http://localhost:8080/catalog/search?q=jacket"             
# -> [{"id":"p_001",...}, {"id":"p_003",...}]

# Now try the query that motivated this chapter:
curl "http://localhost:8080/catalog/search?q=warm%20jacket%20under%20\$100"
# -> []                                                          

# ── Automated checks (same four calls, pass/fail reported) ───────────────────

PASS=0
FAIL=0

green()  { echo -e "\033[32m✓  $*\033[0m"; }
red()    { echo -e "\033[31m✗  $*\033[0m"; }
header() { echo -e "\n\033[1m$*\033[0m"; }

check() {
    local label="$1" url="$2" expected="$3"
    local body
    body=$(curl -sf "$url" || echo "CURL_FAILED")
    if echo "$body" | grep -q "$expected"; then
        green "$label"
        PASS=$((PASS + 1))
    else
        red "$label  (got: $body)"
        FAIL=$((FAIL + 1))
    fi
}

header "Running smoke tests"

check "Gateway health" \
      "$BASE_URL/health" \
      '"status":"ok"'

check "Exact product lookup  p_001" \
      "$BASE_URL/catalog/products/p_001" \
      "Merino Wool Jacket"

check "Substring search  q=jacket  (expects 2 results)" \
      "$BASE_URL/catalog/search?q=jacket" \
      "p_001"

body=$(curl -sf "$BASE_URL/catalog/search?q=warm%20jacket%20under%20%24100" || echo "CURL_FAILED")
if [ "$body" = "[]" ]; then
    green "Semantic gap confirmed  q='warm jacket under \$100' → []  (expected)"
    PASS=$((PASS + 1))
else
    red "Semantic gap test unexpected result: $body"
    FAIL=$((FAIL + 1))
fi

header "Results"
echo "  passed: $PASS"
echo "  failed: $FAIL"

if [ "$FAIL" -eq 0 ]; then
    echo -e "\n\033[32mAll checks passed. The skeleton is running.\033[0m"
    exit 0
else
    echo -e "\n\033[31m$FAIL check(s) failed. Common fixes:\033[0m"
    echo "  • Postgres still initialising  → wait 10 s and rerun"
    echo "  • Port 8080 in use             → change in docker-compose.yml"
    echo "  • Docker low on memory         → allocate ≥ 4 GB in Docker Desktop"
    exit 1
fi
