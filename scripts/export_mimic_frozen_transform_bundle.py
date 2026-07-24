#!/usr/bin/env python3
"""Export access-controlled MIMIC transforms for pure eICU evaluation.

This command reads restricted MIMIC-derived rows and writes a DERIVED_SENSITIVE
artifact. Run it only in an authorized environment and keep the output outside
the public repository.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


PROJECT_ID = "mimic-study-498508"
MIMIC_DATASET = "non_traumatic_sah_study"
ROOT = Path(__file__).resolve().parents[1]
VALIDATION_SCRIPT = ROOT / "scripts" / "15_run_eicu_external_validation.py"


def load_validation_module():
    spec = importlib.util.spec_from_file_location(
        "eicu_external_validation_export_support", VALIDATION_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {VALIDATION_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a private frozen MIMIC transform bundle."
    )
    parser.add_argument("--project", default=PROJECT_ID)
    parser.add_argument("--mimic-dataset", default=MIMIC_DATASET)
    parser.add_argument("--location", default="US")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output.expanduser().resolve()
    if output.is_relative_to(ROOT):
        raise SystemExit(
            "Refusing to write DERIVED_SENSITIVE transforms inside the public repository."
        )
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing artifact: {output}")
    if not output.parent.is_dir():
        raise SystemExit(f"Output parent directory does not exist: {output.parent}")

    from google.cloud import bigquery

    validation = load_validation_module()
    client = bigquery.Client(project=args.project, location=args.location)
    table = f"{args.project}.{args.mimic_dataset}.phenotype_cluster_assignments"
    mimic = validation.read_table(client, table)
    primary = mimic[
        mimic["phenotype_solution"].fillna("").eq("primary_log_pca_kmeans_k3")
    ].copy()
    if primary.empty:
        raise SystemExit(
            "No primary_log_pca_kmeans_k3 rows found; refusing to export an ambiguous transform."
        )
    primary = primary.dropna(subset=["phenotype"])

    pipelines = {
        "primary": validation.fit_frozen_mimic_pipeline(
            primary, validation.FEATURES
        ),
        "hb_free": validation.fit_frozen_mimic_pipeline(
            primary, validation.HB_FREE_FEATURES
        ),
        "inr_free": validation.fit_frozen_mimic_pipeline(
            primary, validation.INR_FREE_FEATURES
        ),
    }
    payload = {
        "artifact_version": "1.0",
        "artifact_class": "DERIVED_SENSITIVE",
        "source_commit": args.source_commit,
        "source_run_id": args.source_run_id,
        "source_table": table,
        "transforms": {
            name: validation.frozen_pipeline_to_dict(pipeline)
            for name, pipeline in pipelines.items()
        },
    }
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output.chmod(0o600)
    print(f"Wrote access-controlled transform bundle: {output}")
    print("Do not commit, upload, or publish this DERIVED_SENSITIVE artifact.")


if __name__ == "__main__":
    main()
