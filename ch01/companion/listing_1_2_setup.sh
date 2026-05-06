#!/usr/bin/env bash
# Listing 1.2 — Setting up the project.
#
# Run this once before working through the rest of the chapter.

set -euo pipefail

# Create the project directory
mkdir -p ai-native-infra/ch01
cd ai-native-infra/ch01

# Create a virtual environment
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

# Install dependencies
pip install google-generativeai==0.8.0 pydantic==2.10.0
