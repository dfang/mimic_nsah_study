#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
command_args=("$@")

usage() {
  cat <<'USAGE'
Usage: ./scripts/run_non_traumatic_sah_bigquery_pipeline.sh [pipeline-options] [cohort-sql-options]

Runs:
  1. scripts/12_run_non_traumatic_sah_cohort_sql.py
  2. scripts/13_run_non_traumatic_sah_analysis.py

Output is printed to the console and saved to:
  dist/analysis_result.md

Pipeline options:
  --sql-only             Run only the cohort SQL step.
  --analysis-only        Run only the Python analysis step.
  --date YYYYMMDD        Deprecated legacy option; the value is ignored.

Common options passed to the cohort SQL step:
  --dry-run              Validate the SQL job without creating tables.
  --project PROJECT      BigQuery project. Default: mimic-study-498508.
  --location LOCATION    BigQuery location. Default: US.
  --sql-file SQL_FILE    SQL file. Default: 10_create_non_traumatic_sah_cohort.sql.
USAGE
}

run_sql=1
run_analysis=1
sql_only=0
analysis_only=0
sql_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --sql-only)
      sql_only=1
      run_analysis=0
      shift
      ;;
    --analysis-only)
      analysis_only=1
      run_sql=0
      shift
      ;;
    --date)
      if [[ $# -lt 2 || ! "$2" =~ ^[0-9]{8}$ ]]; then
        echo "Usage: --date requires a legacy YYYYMMDD value." >&2
        exit 2
      fi
      echo "Warning: --date is deprecated and ignored; output is dist/analysis_result.md." >&2
      shift 2
      ;;
    *)
      sql_args+=("$1")
      shift
      ;;
  esac
done

if [[ "$sql_only" -eq 1 && "$analysis_only" -eq 1 ]]; then
  echo "Cannot combine --sql-only and --analysis-only." >&2
  exit 2
fi

mkdir -p dist
output_file="dist/analysis_result.md"
temporary_file="$(mktemp "dist/.analysis_result.XXXXXX.md")"

{
  printf '# Non-traumatic SAH BigQuery Analysis Result\n\n'
  printf 'Generated at: %s\n\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Command: `%s`\n\n' "$0 ${command_args[*]}"
  printf '```text\n'
} > "$temporary_file"

set +e
(
  set -e
  if [[ "$run_sql" -eq 1 ]]; then
    python3 scripts/12_run_non_traumatic_sah_cohort_sql.py ${sql_args[@]+"${sql_args[@]}"}
  fi

  if [[ "${#sql_args[@]}" -gt 0 ]]; then
    for arg in "${sql_args[@]}"; do
      case "$arg" in
        --dry-run)
          exit 0
          ;;
      esac
    done
  fi

  if [[ "$run_analysis" -eq 1 ]]; then
    python3 scripts/13_run_non_traumatic_sah_analysis.py
  fi
) 2>&1 | tee -a "$temporary_file"
pipeline_status=("${PIPESTATUS[@]}")
set -e

printf '\n```\n' >> "$temporary_file"

producer_status="${pipeline_status[0]}"
tee_status="${pipeline_status[1]}"
if [[ "$producer_status" -ne 0 || "$tee_status" -ne 0 ]]; then
  failure_status="$producer_status"
  if [[ "$failure_status" -eq 0 ]]; then
    failure_status="$tee_status"
  fi
  printf 'Pipeline failed; temporary log retained at: %s\n' "$temporary_file" >&2
  exit "$failure_status"
fi

mv -f "$temporary_file" "$output_file"
