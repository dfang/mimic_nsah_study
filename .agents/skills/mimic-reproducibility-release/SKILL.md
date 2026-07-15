---
name: mimic-reproducibility-release
description: Prepare and audit reproducible MIMIC research releases. Use when freezing an analysis, sharing publication code, packaging SQL/Python/R/notebooks, recording environments and seeds, mapping pipeline DAGs, hashing code and artifacts, tracing manuscript results, or separating public reproducibility materials from restricted patient-level data.
---

# MIMIC Reproducibility Release

Create a release that can reproduce reported results without disclosing restricted MIMIC data. Treat reproducibility as a traceable chain from source version and code to each published table, figure, and estimate.

Apply `mimic-data-governance` before inventorying contents. Metadata-only inventory must precede content reads, and any uncertain artifact inherits the restricted classification until reviewed.

## Define the release boundary

1. Inventory SQL, Python, R, notebooks, configuration, codebooks, model objects, tables, figures, and manuscript outputs.
2. Classify every artifact as public, restricted, generated-public, or excluded-with-reason.
3. Keep public code and documentation physically separate from patient-level data, credentials, query caches, row-level logs, trained artifacts that may encode sensitive data, and restricted derived datasets.
4. Copy `assets/templates/run-manifest.yaml`, `assets/templates/artifact-provenance.csv`, and `assets/templates/pipeline-dag.md` into the study release workspace.

Read `references/release-checklist.md` before declaring a release complete.

## Freeze the computational environment

- Record operating system, architecture, runtime versions, package managers, and external service versions.
- Commit an exact environment lock appropriate to the project, such as `uv.lock`, a fully resolved Python lock, `renv.lock`, or a container digest. A loose dependency list is not an exact lock.
- Record the BigQuery SQL dialect, MIMIC and linked-module versions, derived-concept provenance, and relevant mimic-code commit or release.
- Record required environment-variable names without their values. Never package credentials or service-account keys.

## Make execution deterministic

- Record every random seed and seed location across Python, R, model libraries, resampling, imputation, clustering, and train/test splitting.
- Document nondeterministic operations and hardware-dependent behavior that cannot be eliminated.
- Persist cohort/split logic in code. Do not publish patient identifiers or split membership derived from restricted records.
- For notebooks, restart the runtime and execute from a clean state in order. Fail on hidden-state dependencies, stale outputs, or manual steps that are not documented.

## Map the pipeline DAG

- Give every stage a stable ID and record its command, code entry point, parameters, dependencies, inputs, outputs, and expected checks.
- Distinguish source-data extraction, cohort construction, features, analysis, sensitivity analyses, tables, and figures.
- Make all manuscript outputs traceable to one or more DAG stages.
- Record manual review steps as explicit nodes rather than silently omitting them.

## Hash and trace artifacts

- Record the Git commit and cryptographic hashes for SQL, analysis code, lockfiles, configuration, and shareable outputs.
- Hash the exact files used for the release, not a later working-tree state.
- Keep restricted-artifact hashes in a private manifest when even filenames, row counts, or metadata could disclose sensitive information.
- Link each reported estimate, table, and figure to its generating stage, script/notebook, parameters, and run ID in the provenance table.
- Never claim bitwise reproducibility when only conceptual or statistical reproducibility was verified.

## Run language and notebook QC

- Python: run the project's formatter/linter, static checks, tests, and a clean end-to-end execution where available.
- R: restore the locked environment, run tests and checks appropriate to the project, and execute analysis from a clean session.
- Notebooks: run all cells from a clean kernel; remove patient-level outputs and hidden credentials before public release.
- SQL: validate syntax or dry-run, record source versions, verify row grain and checkpoint counts, and confirm no restricted rows are exported.
- Compare regenerated tables, figures, and primary estimates with the manuscript and explain every expected tolerance or difference.

## Publish safely

- Include only code, synthetic examples, aggregate outputs cleared for release, environment metadata, and reproducibility instructions in the public package.
- State that users must obtain their own authorized MIMIC access and cannot reconstruct the study from bundled patient data.
- Document how restricted inputs are recreated by authorized users.
- Verify the repository and release contain no secrets, absolute personal paths, row-level samples, notebook outputs, or local caches.
- If the public release cannot recreate a result without unavailable private transformations, disclose that limitation instead of labeling the release fully reproducible.

## Completion evidence

Report the release ID and Git commit, environment-lock status, clean-run result, primary-result comparison, public/restricted separation check, provenance coverage, hashes produced, and all remaining reproducibility gaps.
