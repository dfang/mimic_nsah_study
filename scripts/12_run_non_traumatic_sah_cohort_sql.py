#!/usr/bin/env python3
"""Run the non-traumatic SAH cohort BigQuery SQL from this repository.

This wrapper lets Codex or a local terminal execute the same SQL file that is
normally run in the BigQuery console/notebook environment.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path


DEFAULT_PROJECT_ID = "mimic-study-498508"
DEFAULT_LOCATION = "US"
DEFAULT_SQL_FILE = "10_create_non_traumatic_sah_cohort.sql"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Submit 10_create_non_traumatic_sah_cohort.sql to BigQuery."
    )
    parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT_ID,
        help=f"Billing/project ID for the BigQuery job. Default: {DEFAULT_PROJECT_ID}",
    )
    parser.add_argument(
        "--location",
        default=DEFAULT_LOCATION,
        help=f"BigQuery job location. Default: {DEFAULT_LOCATION}",
    )
    parser.add_argument(
        "--sql-file",
        default=DEFAULT_SQL_FILE,
        help=f"SQL file to run. Default: {DEFAULT_SQL_FILE}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the query and estimate bytes without executing it.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from google.cloud import bigquery
        from google.auth.exceptions import DefaultCredentialsError
    except ImportError as exc:
        raise SystemExit(
            "Missing Python dependency: google-cloud-bigquery.\n"
            "Install project runtime dependencies with:\n"
            "  python3 -m pip install -r scripts/requirements-bigquery.txt\n"
            "Then rerun this script with the same python3 executable."
        ) from exc

    sql_path = Path(args.sql_file)
    sql = sql_path.read_text(encoding="utf-8")

    try:
        client = bigquery.Client(project=args.project, location=args.location)
    except DefaultCredentialsError as exc:
        raise SystemExit(
            "Google Application Default Credentials were not found.\n"
            "The Python BigQuery client does not use plain `gcloud auth login` credentials.\n"
            "Run once:\n"
            f"  gcloud auth application-default login --project={args.project}\n"
            "Then rerun this script. Alternatively set GOOGLE_APPLICATION_CREDENTIALS "
            "to a service account JSON path."
        ) from exc
    job_config = bigquery.QueryJobConfig(dry_run=args.dry_run, use_query_cache=False)

    print(f"Project: {args.project}")
    print(f"Location: {args.location}")
    print(f"SQL file: {sql_path}")

    job = client.query(sql, job_config=job_config, location=args.location)

    if args.dry_run:
        print(f"Dry run OK. Estimated bytes processed: {job.total_bytes_processed:,}")
        return

    print(f"BigQuery job: {job.job_id}")
    print("Cohort SQL submitted. Waiting for BigQuery to finish...")

    started = time.monotonic()
    last_report = started
    while not job.done():
        now = time.monotonic()
        if now - last_report >= 30:
            elapsed = int(now - started)
            print(f"Still running BigQuery job {job.job_id}... elapsed {elapsed}s")
            last_report = now
        time.sleep(5)
        job.reload()

    job.result()
    elapsed = int(time.monotonic() - started)
    print(f"Cohort SQL completed in {elapsed}s.")


if __name__ == "__main__":
    main()
