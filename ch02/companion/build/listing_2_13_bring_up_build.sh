#!/usr/bin/env bash
# listing_2_13 — bring up the skeleton.
# Run from the build/ directory:
#
#   cd ch02/companion/build
#   bash listing_2_13_bring_up_build.sh
#
# Prerequisites: Docker Desktop running, GEMINI_API_KEY exported.

set -euo pipefail

COMPOSE_DIR="$(dirname "$0")"
cd "$COMPOSE_DIR"

docker compose -f listing_2_9_docker_compose.yml up -d --build  #A

# Wait ~10 seconds for Postgres to initialize, then:
echo "Waiting 12 s for Postgres to initialise…"
sleep 12

#A Build images and start all seven containers in detached mode.
