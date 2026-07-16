# Submission Manifest

## Target

- Journal: Intensive Care Medicine
- Article type: Original Paper
- Stage: Initial submission preparation
- Requirements retrieved on: 2026-07-16
- Authoritative instructions: https://link.springer.com/journal/134/submission-guidelines
- Package verdict: **NOT READY — REVISE**

## Upstream gates

| Gate | Status | Verdict/manifest artifact | SHA-256 | Open blocking | Open major | Checked on |
| :--- | :--- | :--- | :--- | ---: | ---: | :--- |
| manuscript_review | Complete | `manuscript_review_report.md` | `b059803912f1c3402767f903750bb7a75c7a57d756078e103da3d6a55f0c0ec0` | 3 | 4 | 2026-07-16 |
| reproducibility_release | Not passed | Draft `reproducibility/bundles/release.yaml`; not immutable/frozen | `1be202f6631995a924839a11b5e2271196b92fb0c712ff34e67933264b9645a6` | 1 | Not assessed | 2026-07-16 |

## Live requirements

| Requirement | Evidence/file | Status |
| :--- | :--- | :--- |
| Original Paper, main text <=3,000 words | English canonical manuscript, approximately 2,060 words including declarations and captions | Pass |
| Structured abstract 150-250 words | English abstract: 242 words | Pass |
| Take-home message <=65 words | English take-home message: 63 words | Pass |
| 3-5 keywords | Five keywords | Pass |
| <=30 references | 18 cited references | Pass pending citeproc render |
| Maximum five illustrations, normally three figures and two tables | Three main figures; cohort flow moved to ESM | Pass |
| STROBE/RECORD reporting checklist | `strobe_checklist.md`; `record_checklist.md` | Prepared; author review/open items remain |
| Title page, authors, affiliations, corresponding email, ORCID | Not available | Blocking |
| CRediT roles and ICMJE disclosure forms | Not available | Blocking |
| Ethics, consent, funding, conflicts, availability statements | Placeholders remain | Blocking |
| AI-use disclosure when generative tools were used | Manuscript Declarations | Drafted; author approval required |
| Editable source, journal-ready figures, and PDF | Referenced figures now have 600 dpi PNG and vector PDF; DOCX absent and manuscript/ESM PDFs stale | Blocking on editable source and rendered documents |

## File inventory

| File | Purpose | SHA-256 | Required | Status |
| :--- | :--- | :--- | :---: | :--- |
| `manuscript_non_traumatic_sah_phenotypes.md` | Canonical English manuscript | `3a13e5bbc01b8fdf9106042f544399381317334be8312d56d45dae5b9fb53a47` | Yes | Content revised; author fields/render pending |
| `manuscript_non_traumatic_sah_phenotypes_cn.md` | Chinese reference manuscript | `0c14a7bfac8de51c10315e0a6ddf17ff2c22a13aa7479a5ece0bd79fa4d75c90` | No | Synchronized reference version |
| `electronic_supplementary_material.md` | ESM source | `6e768d2d9d2c2e4705d4303349ba1a877b92db33780acbd61707a836a4043cc2` | Yes | Content prepared; title-page details/render pending |
| `references.bib` | Verified bibliography | `207f4b04e345868d0595572f937f7829014a62278a8889b270182724312ac583` | Build input | Static checks pass; render pending |
| `journal.csl` | ICM parent citation style | `2f39b2c93cf7a90cb41c72a2945700c4d227ad233682d7fe843c77364a11ba82` | Build input | Pinned and verified |
| `strobe_checklist.md` | STROBE mapping | `e1448467c36ce3d226723f721e6c9dedd653151c252e79fa33aa4297f98dfb73` | Yes | Author review pending |
| `record_checklist.md` | RECORD extension mapping | `dd1236ee698383edb250d2cc69c64e3dc38f948aff6259c0e2c32f5811fcb917` | Yes | Open items documented |
| `author_completion_checklist.md` | Single author/reanalysis handoff list | `ffc57d9409237c2a7e980b38c19261af198be8a1bcc6592361e794c0cd9c1ec1` | Internal | Current |

## Blockers

- Complete the author/title-page/declaration/ethics package and ICMJE forms.
- Resolve or formally accept the authorized reanalysis items in `author_completion_checklist.md`.
- Pass an immutable reproducibility-release audit.
- Render and visually inspect citations, DOCX/PDF, and ESM; use the new vector/600 dpi figures and do not use the current stale manuscript PDFs.
