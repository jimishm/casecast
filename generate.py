#!/usr/bin/env python3
"""
CaseCast vignette generator.

Usage:
    python generate.py <fhir_bundle.json> [<fhir_bundle2.json> ...]
    python generate.py --dir <synthea_output_dir>

Output: one JSON vignette per patient, written to ./output/vignettes/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from casecast import generate_narrative, parse_bundle


def process_file(fhir_path: Path, out_dir: Path) -> None:
    if fhir_path.name.startswith(("hospital", "practitioner")):
        return  # skip non-patient files

    print(f"  Parsing   {fhir_path.name}...", end=" ", flush=True)
    data = parse_bundle(fhir_path)
    print(f"({data.demographics.age}yo {data.demographics.sex}, {len(data.active_conditions)} conditions)", end=" ")

    print("generating narrative...", end=" ", flush=True)
    vignette = generate_narrative(data)

    out_path = out_dir / f"{data.patient_id}.json"
    out_path.write_text(json.dumps(vignette.model_dump(), indent=2))
    print(f"→ {out_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate clinical vignettes from Synthea FHIR bundles.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("files", nargs="*", type=Path, help="FHIR bundle JSON files", default=[])
    group.add_argument("--dir", type=Path, help="Directory containing FHIR bundle JSON files")
    args = parser.parse_args()

    fhir_files: list[Path] = []
    if args.dir:
        fhir_files = sorted(args.dir.glob("*.json"))
    else:
        fhir_files = args.files

    if not fhir_files:
        print("No FHIR files found.", file=sys.stderr)
        sys.exit(1)

    out_dir = Path("output/vignettes")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"CaseCast: generating vignettes for {len(fhir_files)} file(s)\n")
    for fhir_path in fhir_files:
        try:
            process_file(fhir_path, out_dir)
        except Exception as e:
            print(f"  ERROR processing {fhir_path.name}: {e}", file=sys.stderr)

    print(f"\nDone. Vignettes written to {out_dir}/")


if __name__ == "__main__":
    main()
