# Reproducibility Release Audit

**Release ID:** MIMIC-NSAH-PHENO-01-draft-20260716
**Status:** BLOCKED / draft only
**Reproducibility level achieved:** Conceptual. Computational and statistical reproduction have not been demonstrated from a clean environment.

## Source and environment

- [x] MIMIC-IV 3.1 and eICU-CRD 2.0 are explicit.
- [ ] Exact source access/extraction dates and BigQuery job provenance are recorded.
- [ ] MIMIC-Code/derived-concept release or commit is recorded.
- [x] Git commit and dirty-worktree status are recorded.
- [ ] Python dependencies are exactly locked; the current requirement file is not a lock.
- [x] GoogleSQL and local tool versions are recorded.
- [x] Required environment-variable values are not included.

## Determinism and execution

- [x] Known random seeds and locations are registered.
- [x] Nondeterministic and grouping limitations are documented.
- [x] Pipeline stages map the reported result path.
- [x] Twenty-five focused repository tests pass, and public Python entry points compile.
- [ ] An authorized clean end-to-end run has completed.
- [ ] SQL dry-run, row-grain, and time-window QC evidence is attached.
- [ ] Regenerated results have been compared with the manuscript.

## Provenance

- [x] Principal SQL, Python, manuscript, and reference files have draft hashes.
- [x] Manuscript components map to DAG stages.
- [x] Referenced figures were regenerated as 600 dpi PNG plus vector PDF and visually reviewed.
- [ ] Every table and figure has a final immutable hash and generating run ID.
- [ ] The worktree is clean and the release commit/tag is frozen.

## Data governance

- [x] Public code and restricted data boundaries are documented.
- [x] The draft public package contains no intentionally included patient-level rows or credentials.
- [x] Automated secret/path scan of the declared public/review scope found no matching credential, private-key, token, password, or absolute-user-path pattern.
- [ ] Aggregate table/figure disclosure review is recorded.
- [ ] Derived-data/model release risk is formally assessed where applicable.
- [x] Users are instructed to obtain their own authorized data access.

## Release verdict

Do not label this repository fully reproducible or submission-ready until the unchecked items are resolved. No bitwise, computational, or statistical reproducibility claim is currently supported.
