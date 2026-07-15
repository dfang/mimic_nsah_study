# Non-traumatic SAH manuscript citation update design

## Objective

Perform a targeted citation update for the English and Chinese non-traumatic
SAH phenotype manuscripts. Verify the existing references, add evidence for
material uncited claims, and produce an auditable, citation-aware manuscript
package without changing study results or statistical estimates.

## Inputs

- `/Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes.md`
- `/Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes_cn.md`
- Target journal: *Intensive Care Medicine*
- Review type: targeted citation update, not a systematic review
- Evidence current through: search date recorded during execution

The user confirmed current MIMIC/PhysioNet authorization and that both inputs
contain disclosure-reviewed aggregate results without patient-level data,
unsafe small cells, or sensitive derived data.

## Approach

1. Build a paragraph-level claim inventory for the Introduction, data-source
   and reporting portions of Methods, and literature-dependent statements in
   the Discussion.
2. Reconcile the 13 legacy references only when an authoritative identity can
   be established. Do not guess a legacy number-to-record mapping.
3. Search PubMed/MEDLINE for missing evidence. Use DOI registries, publisher
   pages, and official database or guideline records to verify identity and
   metadata. Record exact queries, filters, dates, and raw result counts.
4. Assign stable Pandoc citation keys after verification. Use the same keys in
   both language versions.
5. Generate `references.bib` only from bibliography-eligible records. Preserve
   unresolved records in the citation-verification table with an exclusion
   reason or manuscript source placeholder.
6. Obtain the *Intensive Care Medicine* CSL only from the official curated CSL
   repository and check its journal identity and upstream source. If current
   journal style provenance cannot be verified, omit `journal.csl` and record
   the requirement instead of guessing.
7. Replace hand-maintained numbered reference lists with Pandoc citations and
   citeproc-owned reference generation.

## Editing boundaries

- Preserve every study result, denominator, estimate, confidence interval,
  method choice, and interpretation unless a citation-specific wording change
  is required to make a claim accurately reflect its source.
- Do not add citations to self-generated numerical results merely to make them
  appear externally supported.
- Do not introduce treatment-effect or causal language.
- Keep the Chinese and English evidence mappings synchronized.
- Leave explicit placeholders for missing author declarations, ethics wording,
  or citations that cannot be verified.

## Outputs

Write the updated package directly into `/Users/fang/code/mimic_asah_study/dist/`
without a date subdirectory, as explicitly requested by the user:

- `manuscript_non_traumatic_sah_phenotypes_cited.md`
- `manuscript_non_traumatic_sah_phenotypes_cn_cited.md`
- `references.bib`
- `journal.csl`, only if provenance is verified
- `literature_search_log.md`
- `literature_evidence_table.csv`
- `citation_verification.csv`
- `citation_key_map.csv`
- `citation_update_report.md`
- updated generation information in `readme.txt`

The original manuscripts remain unchanged.

## Verification

- Confirm every manuscript citation key exists exactly once in
  `references.bib` and every bibliography record has a unique key.
- Check DOI and PMID resolution status and retain conflicts or missing records
  explicitly.
- Check that English and Chinese manuscripts use the same evidence record for
  equivalent claims.
- Run Pandoc with citeproc and the verified CSL when available; inspect build
  errors and unresolved citations.
- Report intentionally uncited bibliography records, unsupported claims,
  inaccessible full texts, search limitations, and deviations from this design.

## Scope exclusions

- No new statistical analysis or validation of manuscript numerical results.
- No systematic-review completeness claim.
- No publication of patient-level or sensitive derived MIMIC/eICU artifacts.
- No final submission-ready claim before the required independent
  `mimic-review` journal-reviewer gate.
