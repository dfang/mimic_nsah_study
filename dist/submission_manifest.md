# Submission Manifest

## Target

- Journal: Intensive Care Medicine
- Article type: Original Paper
- Stage: Initial submission preparation
- Requirements retrieved on: 2026-07-16
- Authoritative instructions: https://link.springer.com/journal/134/submission-guidelines
- Package verdict: **NOT READY — AUTHOR/PRODUCTION BLOCKED**
- English/Chinese cited-manuscript reconciliation checked on: 2026-07-23

## Upstream gates

| Gate | Status | Verdict/manifest artifact | SHA-256 | Open blocking | Open major | Checked on |
| :--- | :--- | :--- | :--- | ---: | ---: | :--- |
| manuscript_review | Scientific content READY | `manuscript_review_report.md` | `3f0bd49b5e1bc8e81f5cc2ef8ba45395c9597ad8ab4529b722b485f722a0f051` | 0 scientific-content blockers | 0 | 2026-07-23 |
| reproducibility_release | Analysis frozen; reporting corrected | `reproducibility/bundles/release.yaml`; tag `analysis-freeze-v1.0.0` | `476410239287950c144074e677b610920758f20288322ad0e676df230a00056a` | 0 analysis-freeze blockers | Submission production remains open | 2026-07-23 |

The 2026-07-23 five-round review resolved the identified Purpose/Methods/Results/Conclusion inconsistencies against frozen aggregate evidence and aligned the Chinese cited manuscript and ESM. The scientific content gate is READY. A new production review is still required after author metadata and final rendering are available.

## Live requirements

| Requirement | Evidence/file | Status |
| :--- | :--- | :--- |
| Original Paper, main text <=3,000 words | Reviewed English Markdown: 2,640 whitespace-delimited tokens including YAML, headings, abstract, declarations, and captions; Introduction through Conclusion is 2,039 words | Pass |
| Structured abstract 150-250 words | English abstract: 250 words | Pass |
| Take-home message <=65 words | English take-home message: 59 words | Pass |
| 3-5 keywords | Five keywords | Pass |
| <=30 references | 18 cited references | Pass static checks and Pandoc citeproc preflight; final render inspection pending |
| Maximum five illustrations, normally three figures and two tables | Two main figures; cohort flow moved to ESM; mismatched severity-score artwork excluded | Pass |
| STROBE/RECORD reporting checklist | `strobe_checklist.md`; `record_checklist.md` | Prepared; author review/open items remain |
| Title page, authors, affiliations, corresponding email, ORCID | Not available | Blocking |
| CRediT roles and ICMJE disclosure forms | Not available | Blocking |
| Ethics, consent, funding, conflicts, availability statements | Placeholders remain | Blocking |
| AI-use disclosure when generative tools were used | Manuscript Declarations | Drafted; author approval required |
| Editable source, journal-ready figures, and PDF | Referenced figures now have 600 dpi PNG and vector PDF; DOCX absent and manuscript/ESM PDFs stale | Blocking on editable source and rendered documents |

## File inventory

| File | Purpose | SHA-256 | Required | Status |
| :--- | :--- | :--- | :---: | :--- |
| `manuscript_non_traumatic_sah_phenotypes_cited.md` | Reviewed English submission manuscript | `73aafe9a10f9f21c248fe6a204012024f1aaded1400f0c9b05b25348591b3088` | Yes | Scientific content READY; author fields and fresh render pending |
| `manuscript_non_traumatic_sah_phenotypes_cn_cited.md` | Aligned Chinese reference manuscript | `77d1ac9b36fca0358036d93757508545a5a751eb40bfc87bfeb0329027e67c9d` | No | Structure, citations, figures, quantitative results, cohort rules, and interpretation boundaries aligned |
| `electronic_supplementary_material.md` | ESM source | `143202510b96006a627327aab9de153f330e32c24e3a4494b3091d526ea6ccfc` | Yes | Main model, eICU missingness denominators, time-to-event boundary, and figure numbering reconciled; render pending |
| `references.bib` | Verified bibliography | `207f4b04e345868d0595572f937f7829014a62278a8889b270182724312ac583` | Build input | Static checks and Pandoc citeproc preflight pass; final render inspection pending |
| `journal.csl` | ICM parent citation style | `2f39b2c93cf7a90cb41c72a2945700c4d227ad233682d7fe843c77364a11ba82` | Build input | Pinned and verified |
| `strobe_checklist.md` | STROBE mapping | `23c420160eda601d90922eec3afdba38c221140cd96022b3b9ed3477cf6cc9b5` | Yes | Statistical-method and limitations cross-references synchronized; author review pending |
| `record_checklist.md` | RECORD extension mapping | `63b3cb0cadddf954315c9e1cefe7ce295b69c4f394597a97a23d0ce910df71a2` | Yes | Exploratory transport, missingness, and code-validation limits synchronized |
| `author_completion_checklist.md` | Single author/reanalysis handoff list | `89889bbeb24bc270b246076e8a88f572434eb48121f760b67c4cc5354ce6121b` | Internal | Current |
| `reproducibility/bundles/manuscript.yaml` | Bilingual manuscript-stage bundle | `df48dd7ee508a3dc991b49332cdac812cfa844c7750f6a9baf6d065d693ab35b` | Internal | English/Chinese/ESM/checklist hashes synchronized on 2026-07-23 |

## Blockers

- Complete the author/title-page/declaration/ethics package and ICMJE forms.
- Review and accept the explicitly disclosed residual scientific limitations, including absent manual chart validation and non-clustered regression/eICU uncertainty.
- Obtain final author/institution disclosure approval for public journal release.
- Render and visually inspect citations, DOCX/PDF, and ESM; use the new vector/600 dpi figures and do not use the current stale manuscript PDFs.
