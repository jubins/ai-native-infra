# Chapter 1 Companion Files

Companion folder for **Chapter 1 — The AI-Native Paradigm Shift**.

## Layout

```
companion/
├── README.md
│
├── figures/                    # Pre-rendered PNGs embedded in the chapter
│   ├── figure_1_1.png          # The AI-native spectrum
│   ├── figure_1_2.png          # The four governance principles as a chain
│   ├── figure_1_3.png          # Decision guardrail specification (4-quadrant)
│   └── figure_1_4.png          # Health checker architecture
│
├── figure_code/                # Sources for regenerating artefacts
│   ├── make_figures.py         # matplotlib script that produces every figure
│   └── build_ch01_docx.js      # docx-js script that produced the chapter
│
└── listings/                   # Runnable code for every Listing in the chapter
    ├── listing_1_1_structured_llm_call.py
    ├── listing_1_2_setup.sh
    ├── listing_1_3_naive_health_checker.py
    └── listing_1_4_to_1_9_health_checker.py
```

## Regenerating the figures

The figures use a scholarly Manning-flavoured palette (dark red `#8B2A2A`,
navy `#1E3A5F`, warm beige fills, slate borders) and are rendered with
matplotlib at 200 DPI.

```bash
pip install matplotlib
python figure_code/make_figures.py
# PNGs land in /home/claude/work/figs/ — adjust the output path inside
# make_figures.py if you need them somewhere else.
```

## Regenerating the .docx

The chapter file is produced by a single docx-js build script.

```bash
npm install -g docx
node figure_code/build_ch01_docx.js
# Writes ch01_soni_styled.docx to /home/claude/work/.
# The script reads figures from /home/claude/work/figs/, so run
# make_figures.py first or update the paths inside build_ch01_docx.js.
```

## Running the listings

All listings target Python 3.11 or later.

```bash
# One-time project setup (Listing 1.2)
bash listings/listing_1_2_setup.sh

# After activating the venv:
export GEMINI_API_KEY="your-key-from-aistudio.google.com"

# Listing 1.1 — basic structured LLM call
python listings/listing_1_1_structured_llm_call.py

# Listing 1.3 — naive (deliberately flawed) health checker
python listings/listing_1_3_naive_health_checker.py

# Listings 1.4 – 1.9 — production-shaped health checker with all four
# governance principles in action
python listings/listing_1_4_to_1_9_health_checker.py
```

`listing_1_4_to_1_9_health_checker.py` consolidates the six listings the
chapter walks through (data model, class setup, AI path, regex fallback,
audit logger, and the test harness) into one runnable module so readers
can execute the full example end to end without copy-paste assembly.

## Cost note

Running `listing_1_4_to_1_9_health_checker.py` once issues at most three
Gemini Flash calls (≈ $0.000004 total at early-2026 prices). The free
tier of Google AI Studio comfortably covers all exercises in chapters
1 – 10.
