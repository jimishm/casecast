# CaseCast — Claude Code Context

## Project Overview

CaseCast generates synthetic clinical vignettes for AI ground-truth labeling and medical education. It is a two-stage pipeline:

1. **Synthea** (Java) — simulates patients and exports FHIR R4 bundles
2. **Python layer** — parses FHIR data, calls Claude to generate narrative sections, outputs structured JSON vignettes

The canonical output is a `Vignette` object containing structured clinical data (demographics, conditions, vitals, labs, medications) plus four Claude-generated narrative sections: chief complaint, HPI, review of systems, and physical exam.

## Folder Structure

```
casecast/                  ← this repo (Python layer)
  generate.py              ← CLI entry point
  requirements.txt
  .env                     ← ANTHROPIC_API_KEY (gitignored)
  .env.example
  src/casecast/
    schema.py              ← Pydantic models (ClinicalData, Vignette)
    fhir_parser.py         ← FHIR R4 bundle → ClinicalData
    generator.py           ← ClinicalData → Vignette via Claude API
    __init__.py
  output/vignettes/        ← generated JSON vignettes (gitignored)

../synthea/                ← Synthea fork (Java, separate repo)
  output/fhir/             ← generated FHIR bundles (input to casecast)
```

## Tech Stack

- **Python 3.9+** with type hints (`from __future__ import annotations`)
- **Pydantic v2** for all data models — use `BaseModel`, `Optional`, `model_dump()`
- **Anthropic Python SDK** (`anthropic>=0.89.0`) — use `claude-opus-4-6`, stream responses with `client.messages.stream()`
- **python-dotenv** — load `ANTHROPIC_API_KEY` from `.env` at startup
- **Synthea** (Java 17, separate repo at `../synthea`) — run with `./run_synthea`

## How to Run

```bash
# Generate Synthea patients
cd ../synthea
./run_synthea -p 10 --exporter.fhir.export=true

# Generate vignettes
cd ../casecast
python3 generate.py --dir ../synthea/output/fhir/
```

Output is written to `output/vignettes/<patient_id>.json`.

## Coding Conventions

- **`from __future__ import annotations`** at the top of every file
- **Type hints everywhere** — function signatures, local variables where non-obvious
- **Pydantic models for all data structures** — no plain dicts passed between modules
- **Private helpers prefixed with `_`** — e.g. `_format_vitals()`, `_parse_sections()`
- **Module-level docstrings** on every file explaining its purpose
- **f-strings** for string formatting throughout
- **`pathlib.Path`** for all file paths — no `os.path`
- **`Optional[str] = None`** for nullable fields on Pydantic models
- Inline comments on non-obvious constants (e.g. `# "H", "L", or None`)
- Error handling at the CLI boundary (`generate.py`) — let it bubble up from library code

## Key Data Flow

```
FHIR bundle (.json)
  → parse_bundle()          # fhir_parser.py → ClinicalData
  → generate_narrative()    # generator.py → Vignette (calls Claude)
  → vignette.model_dump()   # written to output/vignettes/<id>.json
```

## Claude API Usage

- Model: `claude-opus-4-6`
- Always stream responses (`client.messages.stream()`)
- Prompt is built in `_build_prompt()` in `generator.py` — edit there to change vignette style or content
- `max_tokens=2048` per vignette — increase if narratives are getting cut off

## What's Next

- Phase 3: Web demo — UI to select conditions, specialty, difficulty, and K cases
- Specialty and complexity metadata tagging on Vignette
- Export formats: PDF for educators, CSV for AI labeling pipelines
- Clinical validation approach
