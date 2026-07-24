# Submission Manifest

## Target and verdict

- Journal: Intensive Care Medicine
- Article type: Original Paper
- Stage: Initial submission preparation
- Authoritative instructions: https://link.springer.com/journal/134/submission-guidelines
- Requirements rechecked: 2026-07-24
- Package verdict: **NOT READY**

The Markdown sources are reconciled to the authorized eICU rerun, but the existing
PDFs predate those changes and are explicitly stale. The package is not
submission-ready: author/title metadata, declarations, institutional
aggregate-disclosure approval, editable DOCX, post-rerun rendering, and independent
review remain open. The authorized immutable-transform eICU rerun and aggregate-only
hospital-level robustness analyses are complete.

## Upstream gates

| Gate | Current status | Evidence | Consequence |
| :--- | :--- | :--- | :--- |
| manuscript_review | `pending_independent_rereview` | `reproducibility/bundles/manuscript-review.yaml` | No READY claim is valid after the 2026-07-24 remediation |
| reproducibility_release | `blocked_external_actions` | `reproducibility/bundles/release.yaml` | Public release approval remains outstanding; the derived-sensitive transform rerun is complete |
| submission | `blocked` | `dist/author_completion_checklist.md` | Do not upload |

## Live requirements

| Requirement | Current evidence | Status |
| :--- | :--- | :--- |
| Original Paper main text <=3,000 words | Main text remains below 3,000 words | Pass |
| Structured abstract <=250 words | 250 words | Pass |
| Take-home message <=65 words | 60 words | Pass |
| 3-5 keywords | Five keywords | Pass |
| <=30 references | 18 citeproc-resolved references | Pass |
| Maximum five illustrations | Two main figures | Pass |
| Editable source | Markdown available; journal-preferred DOCX absent | Blocking |
| Complete title page and author metadata | Not supplied | Blocking |
| CRediT, ICMJE disclosures, ethics, funding, conflicts | Not confirmed by authors/institution | Blocking |
| Aggregate disclosure approval | Not recorded | Blocking |
| Independent final review | Remediation changed scientific/reporting artifacts | Blocking |

## Current file inventory

| File | SHA-256 | Status |
| :--- | :--- | :--- |
| `manuscript_non_traumatic_sah_phenotypes_cited.md` | `a4febac02b5ddb06ef83d6cffdad2736e9c0b6cf2dc17f4f99741de5659fe000` | Current English source; non-submission while gates are open |
| `manuscript_non_traumatic_sah_phenotypes_cn_cited.md` | `d417cd39c0420acf1d8c0ededb6d38084cc29c23ba612d89ea6ac5459f0f639c` | Current Chinese reference source |
| `electronic_supplementary_material.md` | `5fe4228632736c213bb5f77713e168e11815e687ac0dd44bf692110e5e7b3737` | Current ESM source |
| `pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf` | `42e472ce7a80e27c135d7f546cf1212e00ad1f55da89f251f21a57855a767ab3` | Pre-rerun 13-page render; stale |
| `pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf` | `f7a946d0b7d411102abea2ac1e76c1d055edd382c93c4a8da6c67a3477061dc0` | Pre-rerun 11-page reference render; stale |
| `pdf/electronic_supplementary_material.pdf` | `327a28401ba2f8a8f80b34eeb4656f6cd93ac278db75f168931110af83978c09` | Pre-rerun 16-page render; stale |
| `pdf/strobe_checklist.pdf` | `04c929e58d78007de764daecce9abd3ba54f49fd6dc412451efc5e9104965efc` | Current 3-page render |
| `pdf/generation-manifest.yaml` | `7f4e4e526e7ed8b76fc1ab7116454c9914d76bf7aa08e1eff1502389d557d46a` | Records the pre-rerun render and marks it stale against current sources |

## Scientific and governance boundary

- The MIMIC results remain `FROZEN_EXPLORATORY`.
- Stability evidence supports overall partition stability; cluster-specific Jaccard,
  assignment-uncertainty distributions, and multiple-seed summaries are not assessed.
- The 2026-07-24 eICU aggregates come from a pure frozen evaluation using a
  privately hashed transform bundle; they remain exploratory and do not establish
  cluster-boundary replication.
- Exact transform parameters are `DERIVED_SENSITIVE` and must not be published in
  this repository.
- Repository visibility does not substitute for author/institution disclosure approval.
