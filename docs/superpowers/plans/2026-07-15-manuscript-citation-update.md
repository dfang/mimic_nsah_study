# Non-traumatic SAH Manuscript Citation Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce verified, citation-aware English and Chinese NSAH phenotype manuscripts plus an auditable literature evidence package.

**Architecture:** Treat citation identity, evidence suitability, manuscript insertion, and rendering as separate gates. Build one verified record set and one stable key map, then apply the same claim-to-record mapping to both language versions before citeproc validation.

**Tech Stack:** Markdown with Pandoc citations, BibTeX, CSL, PubMed/MEDLINE, authoritative DOI and publisher records, CSV audit artifacts, Pandoc citeproc, POSIX shell and Python standard library for validation.

## Global Constraints

- Process only the two user-approved, disclosure-reviewed aggregate manuscripts.
- Do not alter study denominators, estimates, confidence intervals, methods, or scientific conclusions.
- Review type is a targeted citation update, not a systematic review.
- Do not guess citation identities, DOI values, PMID values, citation keys, or journal style provenance.
- Use identical citation keys for equivalent claims in the English and Chinese manuscripts.
- Preserve the original manuscripts; write suffixed cited copies directly into `/Users/fang/code/mimic_asah_study/dist/` without a date subdirectory.
- Do not publish patient-level or sensitive derived MIMIC/eICU artifacts.
- Do not call the manuscript submission-ready before the independent `mimic-review` journal-reviewer gate.

---

### Task 1: Build the claim and legacy-reference audit

**Files:**
- Read: `/Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes.md`
- Read: `/Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes_cn.md`
- Create: `/Users/fang/code/mimic_asah_study/dist/citation_claim_audit.csv`

**Interfaces:**
- Consumes: the 13 legacy references and literature-dependent claims in both manuscripts.
- Produces: CSV columns `claim_id,section,english_claim,chinese_claim,legacy_reference_number,evidence_needed,status,notes` for Tasks 2 and 4.

- [ ] **Step 1: Inventory static citations and citation-like text**

Run:

```bash
rg -n '^## References|^## 参考文献|^[0-9]+\.|\[@|DOI|PMID' \
  /Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes.md \
  /Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes_cn.md
```

Expected: both manuscripts contain the same 13 hand-numbered references and no Pandoc citation keys.

- [ ] **Step 2: Create the synchronized claim audit**

Record one row for each material external claim in the Introduction, literature-dependent Methods statements, and Discussion. Set `status` to one of `legacy_candidate`, `missing_evidence`, `self_generated_result`, or `no_citation_needed`. Do not assign a paper before identity verification.

- [ ] **Step 3: Validate claim IDs and bilingual coverage**

Run:

```bash
python - <<'PY'
import csv
from collections import Counter
p = '/Users/fang/code/mimic_asah_study/dist/citation_claim_audit.csv'
rows = list(csv.DictReader(open(p, encoding='utf-8')))
ids = [r['claim_id'] for r in rows]
assert rows, 'claim audit is empty'
assert not [k for k, n in Counter(ids).items() if n != 1], 'duplicate claim_id'
assert all(r['english_claim'] and r['chinese_claim'] for r in rows if r['status'] != 'no_citation_needed')
print(f'PASS: {len(rows)} unique claim rows')
PY
```

Expected: `PASS: <N> unique claim rows` with no assertion error.

### Task 2: Run the targeted search and verify evidence records

**Files:**
- Create: `/Users/fang/code/mimic_asah_study/dist/literature_search_log.md`
- Create: `/Users/fang/code/mimic_asah_study/dist/literature_evidence_table.csv`
- Create: `/Users/fang/code/mimic_asah_study/dist/citation_verification.csv`

**Interfaces:**
- Consumes: `citation_claim_audit.csv` and the 13 legacy reference strings.
- Produces: verified record IDs, authoritative metadata, evidence suitability, and bibliography eligibility for Task 3.

- [ ] **Step 1: Define and record the targeted review scope**

Use the scope: adult non-traumatic or aneurysmal SAH; early neuro-systemic physiology, organ dysfunction, anemia/transfusion, neurological and general ICU severity scales, EHR phenotype discovery/transport, MIMIC-IV/eICU provenance, and STROBE/RECORD reporting. Record English-language searches from database inception through 2026-07-15 and state that this is not a systematic review.

- [ ] **Step 2: Search PubMed/MEDLINE reproducibly**

Run separate queries for SAH systemic complications, SAH anemia/transfusion, critical-care phenotyping, source database papers, and scale/reporting records. For every query record database/platform, exact query, search date, coverage end, filters, and raw result count before screening.

- [ ] **Step 3: Verify every retained and legacy record**

Resolve claimed PMIDs in PubMed and claimed DOIs through DOI/publisher records. Cross-check title, authors, journal, year, volume, pages/article number, DOI, PMID, publication status, and correction/retraction notices. Use only `verified`, `partial`, `conflict`, `not_found`, or `not_applicable` statuses.

- [ ] **Step 4: Extract suitability and limitations**

For each retained report fill all required evidence-table fields, including actual population, database/version, design, cohort dates, sample size, time zero/windows, methods, estimates/uncertainty when cited, limitations, and relevance. Label abstract-only assessment explicitly.

- [ ] **Step 5: Validate evidence-table vocabulary and eligibility**

Run:

```bash
python - <<'PY'
import csv
p = '/Users/fang/code/mimic_asah_study/dist/literature_evidence_table.csv'
rows = list(csv.DictReader(open(p, encoding='utf-8')))
allowed = {'verified', 'partial', 'conflict', 'not_found', 'not_applicable'}
for r in rows:
    assert r['doi_status'] in allowed
    assert r['pmid_status'] in allowed
    if r['bibliography_eligible'] == 'yes':
        assert r['citation_key']
        assert r['doi_status'] in {'verified', 'not_applicable'}
        assert r['pmid_status'] in {'verified', 'not_applicable'}
    else:
        assert r['bibliography_exclusion_reason']
print(f'PASS: validated {len(rows)} evidence rows')
PY
```

Expected: `PASS: validated <N> evidence rows` with no assertion error.

### Task 3: Build the verified bibliography and journal style

**Files:**
- Create: `/Users/fang/code/mimic_asah_study/dist/references.bib`
- Create: `/Users/fang/code/mimic_asah_study/dist/citation_key_map.csv`
- Create if verified: `/Users/fang/code/mimic_asah_study/dist/journal.csl`

**Interfaces:**
- Consumes: bibliography-eligible rows from `literature_evidence_table.csv` and `citation_verification.csv`.
- Produces: unique stable keys and renderable bibliography/style artifacts for Tasks 4 and 5.

- [ ] **Step 1: Assign stable keys and export eligible records**

Use `firstauthorYYYYkeyword`; resolve collisions with a deterministic suffix from stable record metadata. Preserve verified DOI and PMID values. Exclude `partial`, `conflict`, and `not_found` identities from `references.bib`.

- [ ] **Step 2: Obtain and verify the ICM CSL**

Fetch the *Intensive Care Medicine* style only from the official Citation Style Language repository. Confirm the CSL title/ID or dependent parent link identifies the target journal, record upstream URL and retrieval date, and preserve the upstream license metadata. If this cannot be confirmed, do not create `journal.csl`; record the missing style requirement in the final report.

- [ ] **Step 3: Check key uniqueness and identifier deduplication**

Run:

```bash
python - <<'PY'
import csv, re
from collections import Counter
root = '/Users/fang/code/mimic_asah_study/dist'
rows = list(csv.DictReader(open(f'{root}/citation_key_map.csv', encoding='utf-8')))
keys = [r['citation_key'] for r in rows]
assert not [k for k, n in Counter(keys).items() if n != 1]
bib = open(f'{root}/references.bib', encoding='utf-8').read()
bibkeys = re.findall(r'^@\w+\{([^,]+),', bib, flags=re.M)
assert Counter(keys) == Counter(bibkeys)
for field in ('doi', 'pmid'):
    vals = [r[field].strip().lower() for r in rows if r[field].strip()]
    assert not [v for v, n in Counter(vals).items() if n != 1], f'duplicate {field}'
print(f'PASS: {len(keys)} unique bibliography records')
PY
```

Expected: `PASS: <N> unique bibliography records`.

### Task 4: Insert synchronized Pandoc citations in both manuscripts

**Files:**
- Create: `/Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes_cited.md`
- Create: `/Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes_cn_cited.md`

**Interfaces:**
- Consumes: claim mappings, `references.bib`, `citation_key_map.csv`, and verified `journal.csl` when available.
- Produces: citation-aware manuscripts for Task 5.

- [ ] **Step 1: Copy the original manuscripts and add metadata**

Add this YAML block to each cited copy, using the verified CSL only when it exists:

```yaml
---
bibliography: references.bib
csl: journal.csl
link-citations: true
reference-section-title: References
---
```

For the Chinese copy use `reference-section-title: 参考文献`.

- [ ] **Step 2: Replace prose-level evidence gaps with verified keys**

Insert citations immediately after the supported claim. Use combined citations such as `[@key1; @key2]` only when each record materially supports that claim. Do not cite self-generated cohort counts, estimates, or sensitivity-analysis results.

- [ ] **Step 3: Remove hand-numbered reference entries**

Keep the References/参考文献 heading only if required for rendering, and remove every manually numbered entry so citeproc exclusively owns inclusion, order, numbering, and formatting.

- [ ] **Step 4: Verify bilingual key synchronization**

Run:

```bash
python - <<'PY'
import re
root = '/Users/fang/code/mimic_asah_study/dist'
paths = [
    f'{root}/manuscript_non_traumatic_sah_phenotypes_cited.md',
    f'{root}/manuscript_non_traumatic_sah_phenotypes_cn_cited.md',
]
sets = []
for p in paths:
    text = open(p, encoding='utf-8').read()
    sets.append(set(re.findall(r'@([A-Za-z0-9_:.+-]+)', text)))
assert sets[0] == sets[1], f'key mismatch: EN-only={sets[0]-sets[1]}, CN-only={sets[1]-sets[0]}'
print(f'PASS: {len(sets[0])} synchronized citation keys')
PY
```

Expected: `PASS: <N> synchronized citation keys`.

### Task 5: Render, audit, and document the citation package

**Files:**
- Create: `/Users/fang/code/mimic_asah_study/dist/citation_update_report.md`
- Modify: `/Users/fang/code/mimic_asah_study/dist/readme.txt`
- Verify: all Task 1–4 outputs

**Interfaces:**
- Consumes: both cited manuscripts, bibliography, CSL, search/evidence/verification tables, and claim audit.
- Produces: final verification evidence and an explicit unresolved-issues report.

- [ ] **Step 1: Check all cited keys resolve and identify unused records**

Run a Python standard-library audit that compares manuscript keys with BibTeX keys. Fail on missing keys; report bibliography records unused by either manuscript as intentionally uncited or remove them.

- [ ] **Step 2: Render both manuscripts with citeproc**

Run:

```bash
cd /Users/fang/code/mimic_asah_study/dist
pandoc manuscript_non_traumatic_sah_phenotypes_cited.md --citeproc -o /tmp/nsah_en_cited.html
pandoc manuscript_non_traumatic_sah_phenotypes_cn_cited.md --citeproc -o /tmp/nsah_cn_cited.html
```

Expected: exit status 0 and no `citation not found` warnings. If Pandoc is unavailable, record the exact missing executable and complete static key validation without claiming render verification.

- [ ] **Step 3: Inspect rendered reference sections**

Confirm that citations appear in order of first use, bibliography entries are generated once, DOI/URL fields render sensibly, and the Chinese manuscript retains Chinese body text while using the same source identities.

- [ ] **Step 4: Write the update report**

Record scope, search date/coverage, retained and excluded legacy references, new sources, unresolved keys or placeholders, intentionally uncited records, citation-verification status, claim provenance, CSL provenance, rendering result, inaccessible full texts, protocol/design deviations, and the requirement for later `mimic-review` journal review.

- [ ] **Step 5: Update generation metadata without overwriting provenance**

Append a Codex citation-update entry to `readme.txt` naming the new artifacts, execution date, source manuscripts, target journal, and verification limitations. Preserve the existing Gemini generation metadata.

- [ ] **Step 6: Run final non-destructive checks**

Run:

```bash
rg -n 'citation not found|\?\?\?|DOI:\s*$|PMID:\s*$|^[0-9]+\.' \
  /Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes_cited.md \
  /Users/fang/code/mimic_asah_study/dist/manuscript_non_traumatic_sah_phenotypes_cn_cited.md \
  /Users/fang/code/mimic_asah_study/dist/references.bib \
  /Users/fang/code/mimic_asah_study/dist/citation_update_report.md
```

Expected: no unresolved-render markers, empty identifiers, or manually numbered bibliography entries. Any deliberate source placeholder must appear in `citation_update_report.md` with its blocking reason.

