# Submission Manifest

## Target

- Journal: Intensive Care Medicine
- Article type: Original Paper
- Stage: Initial submission preparation
- Requirements retrieved on: 2026-07-16
- Authoritative instructions: https://link.springer.com/journal/134/submission-guidelines
- Package verdict: **NOT READY — REVISE**
- English/Chinese cited-manuscript reconciliation checked on: 2026-07-23

## Upstream gates

| Gate | Status | Verdict/manifest artifact | SHA-256 | Open blocking | Open major | Checked on |
| :--- | :--- | :--- | :--- | ---: | ---: | :--- |
| manuscript_review | Complete | `manuscript_review_report.md` | `b059803912f1c3402767f903750bb7a75c7a57d756078e103da3d6a55f0c0ec0` | 3 | 4 | 2026-07-16 |
| reproducibility_release | Analysis frozen | `reproducibility/bundles/release.yaml`; tag `analysis-freeze-v1.0.0` | `dc6cabb8529f17e57ca3106a18332162ce03fd5a6a16b13be7e7746e49cd6bbf` | 0 analysis-freeze blockers | Submission risks remain | 2026-07-16 |

The 2026-07-22 English correction pass resolved the selected Purpose/Methods/Results/Conclusion inconsistencies against frozen aggregate evidence. The Chinese cited manuscript was aligned to that source on 2026-07-23. This is not a replacement for a new independent full-package review after author metadata and final rendering are available.

## Live requirements

| Requirement | Evidence/file | Status |
| :--- | :--- | :--- |
| Original Paper, main text <=3,000 words | Reviewed English Markdown: approximately 2,850 whitespace-delimited tokens including YAML, headings, abstract, declarations, and captions (a conservative superset of journal main text) | Pass |
| Structured abstract 150-250 words | English abstract: 242 words | Pass |
| Take-home message <=65 words | English take-home message: 53 words | Pass |
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
| `manuscript_non_traumatic_sah_phenotypes_cited.md` | Reviewed English submission manuscript | `077136b5e4e83b03f8d21b3b41ae7c03644899c592f97cd2f6c852095aab1d88` | Yes | Purpose/Methods/Results/Conclusion reconciled; mismatched artwork excluded; author fields/render pending |
| `manuscript_non_traumatic_sah_phenotypes_cn_cited.md` | Aligned Chinese reference manuscript | `17171686f3ee6e0989113bbeb4248f9f5b41fb2fc523bebc83777f90526cec71` | No | Structure, citations, figures, quantitative results, and interpretation boundaries aligned on 2026-07-23 |
| `electronic_supplementary_material.md` | ESM source | `8fe8ed083d934e4f5d91c11dbe40b1545b28df9e55b432076249df34f8c1c5c9` | Yes | Synchronized with same-hospital/time-to-event boundary and figure numbering; render pending |
| `references.bib` | Verified bibliography | `207f4b04e345868d0595572f937f7829014a62278a8889b270182724312ac583` | Build input | Static checks and Pandoc citeproc preflight pass; final render inspection pending |
| `journal.csl` | ICM parent citation style | `2f39b2c93cf7a90cb41c72a2945700c4d227ad233682d7fe843c77364a11ba82` | Build input | Pinned and verified |
| `strobe_checklist.md` | STROBE mapping | `699a38284d71c7f9fca8c970fbe4305d6302a976db582f65309e4cfcf7d3ea99` | Yes | Same-hospital association wording and ESM cross-references synchronized; author review pending |
| `record_checklist.md` | RECORD extension mapping | `94435b72a9986c06f4319240f3b42c505f7a48c4a3a09c520b5929290831f7d9` | Yes | Exploratory fixed-transport wording and ESM cross-references synchronized; open items documented |
| `author_completion_checklist.md` | Single author/reanalysis handoff list | `9791f4292a6d0559bb72b036f49980f50a63985b6a64a282e642662c2f8f086f` | Internal | Current |
| `reproducibility/bundles/manuscript.yaml` | Bilingual manuscript-stage bundle | `f459b01ea629104736e37bfb2b0b4b960a82e9cb298ddd7667ad5aaf56c61fa3` | Internal | English/Chinese manuscript hashes synchronized on 2026-07-23 |

## Blockers

- Complete the author/title-page/declaration/ethics package and ICMJE forms.
- Resolve or justify the remaining authorized-design items in `author_completion_checklist.md`, including the post-entry transfusion exclusion and NSAH identification validation.
- Obtain final author/institution disclosure approval for public journal release.
- Render and visually inspect citations, DOCX/PDF, and ESM; use the new vector/600 dpi figures and do not use the current stale manuscript PDFs.
