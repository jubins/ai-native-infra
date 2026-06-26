#!/usr/bin/env bash
# Listing 3.3: discovery_calls.sh — runtime specification discovery.
#
# The chapter shows REST, GraphQL, and gRPC discovery side by side. Only the
# REST path is implemented in this companion repo (the catalog service is
# REST-only). The GraphQL and gRPC commands are included as reference; you
# will need a GraphQL or gRPC service of your own to run them.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"

echo "# REST: fetch the OpenAPI document."
curl -s "${BASE_URL}/openapi.json" | jq '.info'
# => { "title": "Catalog Service", "version": "1.0.0", "description": "..." }

cat <<'EOF'

# GraphQL: introspect the schema (reference only; no GraphQL service in this repo).
# curl -s -X POST http://localhost:8080/catalog/graphql \
#   -H 'Content-Type: application/json' \
#   -d '{"query": "{ __schema { queryType { fields { name description } } } }"}'

# gRPC: list services and describe one of them (reference only; no gRPC service).
# grpcurl -plaintext localhost:50051 list
# grpcurl -plaintext localhost:50051 describe catalog.v1.Catalog
EOF
