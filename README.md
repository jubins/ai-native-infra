# AI-Native Infrastructure

Companion code for *AI-Native Infrastructure* by Jubin Soni, published by Manning Publications Co.

[![ch02 build](https://github.com/jubins/ai-native-infra/actions/workflows/ch02.yml/badge.svg)](https://github.com/jubins/ai-native-infra/actions/workflows/ch02.yml)
[![ch03 build](https://github.com/jubins/ai-native-infra/actions/workflows/ch03.yml/badge.svg)](https://github.com/jubins/ai-native-infra/actions/workflows/ch03.yml)
[![License](https://img.shields.io/badge/license-Manning%20Publications-blue)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Chapter Guide](#chapter-guide)
  - [Chapter 1 — The AI-Native Paradigm Shift](#chapter-1--the-ai-native-paradigm-shift)
  - [Chapter 2 — First Principles and Architectural Patterns](#chapter-2--first-principles-and-architectural-patterns)
  - [Chapter 3 — API Design and Contract Evolution](#chapter-3--api-design-and-contract-evolution)
  - [Appendix A — Shared Setup](#appendix-a--shared-setup)
- [License](#license)

---

## Overview

A practical guide to infrastructure where AI is a core architectural primitive — not bolted on, but built in from the start, explicitly constrained to where it is essential and excluded where deterministic logic remains the right answer. The playbook for what comes after bolting AI onto systems designed without it.

Each chapter folder contains:

- **`companion/listings/`** — standalone runnable files, one per numbered listing in the book
- **`companion/build/`** (chapters 2 and 3) — a runnable Docker Compose platform that evolves across chapters
- **`README.md`** — setup instructions, listing index, and notes specific to that chapter

Code in chapters 2 and 3 is covered by CI smoke tests that run on every push.

---

## Prerequisites

- Python 3.10+
- Docker and Docker Compose (chapters 2 and 3)
- A [Gemini API key](https://aistudio.google.com) — free tier covers all exercises
- `curl`, `jq`, `uuidgen` (chapter 3 smoke tests; pre-installed on macOS)

---

## Chapter Guide

### Chapter 1 — The AI-Native Paradigm Shift

> Introduces the bounded-intelligence envelope: structured LLM calls, deterministic fallbacks, audit logging, and scope limits.

```bash
pip install -r ch01/companion/requirements.txt
export GEMINI_API_KEY="your-key-here"
python ch01/companion/listings/listing_1_1_structured_llm_call.py
```

See [ch01/README.md](ch01/README.md) for the full listing index.

---

### Chapter 2 — First Principles and Architectural Patterns

> Builds a seven-container platform skeleton (gateway, catalog, checkout, orders, Postgres, Redis, Kafka) and demonstrates eight AI-native infrastructure patterns.

```bash
pip install -r appendix_a/requirements.txt
export GEMINI_API_KEY="your-key-here"

# Run standalone listings
python ch02/companion/listings/listing_2_1_string_match.py

# Run the platform skeleton
cd ch02/companion/build
bash listing_2_13_bring_up_build.sh
bash smoke_test.sh
```

See [ch02/README.md](ch02/README.md) for the full listing index and bonus patterns.

---

### Chapter 3 — API Design and Contract Evolution

> Upgrades the catalog service and adds an orders service with structured errors, confidence-carrying responses, AI-generated descriptions, and idempotent writes.

```bash
cd ch03/companion/build
cp .env.example .env        # add GEMINI_API_KEY=your-key-here (optional)
make up
make smoke
```

See [ch03/README.md](ch03/README.md) for the full listing index and smoke test details.

---

### Appendix A — Shared Setup

Shared scaffolding (`ch02_setup.py`) used by chapter 2 standalone listings: the bounded-intelligence envelope, embedding helper, and sample product catalog.

```bash
pip install -r appendix_a/requirements.txt
```

See [appendix_a/README.md](appendix_a/README.md) for details.

---

## License

Copyright (c) Manning Publications Co. All rights reserved.

This repository contains companion code for *AI-Native Infrastructure* by Jubin Soni.
See [LICENSE](LICENSE) for the full terms.
