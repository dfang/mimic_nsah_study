#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  cat <<'USAGE'
Usage: ./scripts/run_non_traumatic_sah_bigquery_pipeline.sh [pipeline-options] [cohort-sql-options]

Runs:
  1. scripts/12_run_non_traumatic_sah_cohort_sql.py
  2. scripts/13_run_non_traumatic_sah_analysis.py

Output is printed to the console and saved to:
  dist/YYYYMMDD/analysis_result.md

Pipeline options:
  --sql-only             Run only the cohort SQL step.
  --analysis-only        Run only the Python analysis step.
  --date YYYYMMDD        Date folder name to output results to. Default: today's date.

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
date_dir=$(date '+%Y%m%d')

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
      if [[ $# -lt 2 ]]; then
        echo "Error: --date requires a YYYYMMDD argument." >&2
        exit 2
      fi
      date_dir="$2"
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

mkdir -p "dist/${date_dir}"
output_file="dist/${date_dir}/analysis_result.md"

close_log_block() {
  printf '\n```\n' >> "$output_file"
}

{
  printf '# Non-traumatic SAH BigQuery Analysis Result\n\n'
  printf 'Generated at: %s\n\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf 'Command: `%s`\n\n' "$0 $*"
  printf '```text\n'
} > "$output_file"

exec > >(tee -a "$output_file") 2>&1
trap close_log_block EXIT

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
