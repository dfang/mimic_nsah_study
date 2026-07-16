# Massive-Transfusion Sensitivity Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the current no-massive-transfusion primary cohort while adding an auditable sensitivity analysis that includes 0–24-hour massive RBC transfusion stays.

**Architecture:** Define one additional eligibility flag in the final BigQuery wide table and route it through the existing Python sensitivity-cohort registry. Lock the cross-file contract with standard-library tests, then align protocol, SAP, and an append-only deviation record without changing the study's `DRAFT_BLOCKED` or exploratory status.

**Tech Stack:** BigQuery Standard SQL, Python 3.12 standard library and existing analysis stack, Markdown governance documents, `unittest`, Git.

## Global Constraints

- Keep `eligible_primary_analysis = core_feature_missing_count <= 2 AND massive_transfusion_24h = 0` unchanged.
- Define `eligible_include_massive_transfusion_sensitivity = core_feature_missing_count <= 2` with no massive-transfusion restriction.
- Do not change age, non-traumatic SAH evidence, ICU-stay selection, ICU length-of-stay, feature windows, missingness threshold, feature set, estimator, dependency, random seed, or outcome definition.
- Treat the inclusive analysis as supportive sensitivity analysis, not co-primary and not a causal transfusion analysis.
- Preserve `freeze_decision: DRAFT_BLOCKED`, `outcome_access_before_freeze: "accessed"`, and exploratory language.
- Record that this decision was made after outcome access; never describe it as pre-outcome prespecification.
- Do not execute BigQuery, regenerate results, or access patient-level data in this implementation.
- Add no dependencies.

---

### Task 1: Lock the cross-file cohort contract with failing tests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_massive_transfusion_sensitivity_contract.py`
- Read: `10_create_non_traumatic_sah_cohort.sql`
- Read: `11_bigquery_notebook_non_traumatic_sah_analysis.py`
- Read after Task 4: `protocol.md`
- Read after Task 4: `sap.md`
- Read after Task 4: `deviations.md`

**Interfaces:**
- Consumes: exact SQL aliases and Python registry names approved in the design.
- Produces: a standard-library regression contract used by Tasks 2–4.

- [ ] **Step 1: Create the local test package marker**

Add the following file exactly so the repository test package cannot be shadowed by an installed top-level `tests` package:

```python
"""Repository-local contract tests."""
```

- [ ] **Step 2: Create the failing contract test**

Add the following file exactly:

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "10_create_non_traumatic_sah_cohort.sql"
PYTHON_PATH = ROOT / "11_bigquery_notebook_non_traumatic_sah_analysis.py"


def wide_table_cases(sql: str) -> dict[str, str]:
    start = "CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` AS"
    end = "FROM `mimic-study-498508.non_traumatic_sah_study.analysis_features_48h`;"
    segment = sql.split(start, 1)[1].split(end, 1)[0]
    return {
        alias: " ".join(body.split())
        for body, alias in re.findall(
            r"CASE\s+(.*?)\s+END AS ([a-z0-9_]+)", segment, flags=re.DOTALL
        )
    }


class SqlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.cases = wide_table_cases(cls.sql)

    def test_primary_exclusion_is_preserved(self) -> None:
        body = self.cases["eligible_primary_analysis"]
        self.assertIn("core_feature_missing_count <= 2", body)
        self.assertIn("massive_transfusion_24h = 0", body)

    def test_inclusive_sensitivity_removes_only_massive_transfusion(self) -> None:
        body = self.cases["eligible_include_massive_transfusion_sensitivity"]
        self.assertEqual(
            body,
            "WHEN core_feature_missing_count <= 2 THEN 1 ELSE 0",
        )

    def test_sql_audit_outputs_include_sensitivity(self) -> None:
        self.assertIn(
            "COUNTIF(eligible_include_massive_transfusion_sensitivity = 1) "
            "AS include_massive_transfusion_sensitivity_rows",
            self.sql,
        )
        self.assertIn("10_sensitivity_include_massive_transfusion", self.sql)


class PythonContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PYTHON_PATH.read_text(encoding="utf-8")

    def test_python_loads_and_registers_sensitivity_flag(self) -> None:
        self.assertGreaterEqual(
            self.source.count('"eligible_include_massive_transfusion_sensitivity"'),
            2,
        )
        self.assertIn(
            '"include_massive_transfusion": '
            '"eligible_include_massive_transfusion_sensitivity"',
            self.source,
        )
        self.assertIn('COHORT_FLAG = "eligible_primary_analysis"', self.source)


class GovernanceContractTests(unittest.TestCase):
    def test_documents_preserve_exploratory_freeze_boundary(self) -> None:
        protocol = (ROOT / "protocol.md").read_text(encoding="utf-8")
        sap = (ROOT / "sap.md").read_text(encoding="utf-8")
        deviations = (ROOT / "deviations.md").read_text(encoding="utf-8")
        for document in (protocol, sap):
            self.assertIn("freeze_decision: DRAFT_BLOCKED", document)
            self.assertIn('outcome_access_before_freeze: "accessed"', document)
            self.assertIn("eligible_include_massive_transfusion_sensitivity", document)
        self.assertIn("DEV-2026-07-16-001", deviations)
        self.assertIn('outcome_access_before_decision: "accessed"', deviations)
        self.assertIn("不得描述为结果揭盲前预设", deviations)
        self.assertIn("支持性敏感性分析", protocol)
        self.assertIn("不用于估计 RBC 输血的因果效应", protocol)
        self.assertIn("支持性而非共同主要分析", sap)
        self.assertIn("不得据此估计 RBC 输血因果效应", sap)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test and verify the intended failures**

Run:

```bash
python3 -m unittest tests/test_massive_transfusion_sensitivity_contract.py -v
```

Expected: the existing primary-exclusion test passes; the inclusive SQL, Python registry, and governance tests fail because the new flag and active-worktree documents are not implemented yet.

- [ ] **Step 4: Commit the failing contract**

```bash
git add tests/__init__.py tests/test_massive_transfusion_sensitivity_contract.py
git commit -m "Lock the transfusion sensitivity cohort contract"
```

Commit body must record that failures are intentional until Tasks 2–4 and that no BigQuery execution was performed.

### Task 2: Add the inclusive sensitivity flag to the BigQuery cohort contract

**Files:**
- Modify: `10_create_non_traumatic_sah_cohort.sql:1391-1393`
- Modify: `10_create_non_traumatic_sah_cohort.sql:1403-1433`
- Modify: `10_create_non_traumatic_sah_cohort.sql:1502-1512`
- Test: `tests/test_massive_transfusion_sensitivity_contract.py`

**Interfaces:**
- Consumes: `core_feature_missing_count` and `massive_transfusion_24h` from `analysis_features_48h`.
- Produces: integer flag `eligible_include_massive_transfusion_sensitivity`, validation alias `include_massive_transfusion_sensitivity_rows`, and flowchart step `10_sensitivity_include_massive_transfusion`.

- [ ] **Step 1: Add a pre-wide-table audit count**

Change the end of the eligibility-count query to:

```sql
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0) AS eligible_primary_analysis_rows,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0 AND icu_los_hours >= 48) AS eligible_48h_los_sensitivity_rows,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0 AND any_rbc_transfusion_48h = 0) AS eligible_no_rbc_sensitivity_rows,
    COUNTIF(core_feature_missing_count <= 2) AS eligible_include_massive_transfusion_sensitivity_rows
```

- [ ] **Step 2: Add the eligibility flag without changing existing flags**

Append this CASE expression after `eligible_no_transfusion_sensitivity`, adding the required comma before it:

```sql
    CASE
        WHEN core_feature_missing_count <= 2 THEN 1
        ELSE 0
    END AS eligible_include_massive_transfusion_sensitivity
```

- [ ] **Step 3: Add the final-table validation count**

Add this expression after the existing no-transfusion sensitivity count:

```sql
    COUNTIF(eligible_include_massive_transfusion_sensitivity = 1) AS include_massive_transfusion_sensitivity_rows,
```

- [ ] **Step 4: Add the flowchart sensitivity row and preserve stable ordering**

Keep the existing `08_sensitivity_icu_los_ge_48h` and `09_sensitivity_no_rbc_48h` rows unchanged, then append:

```sql
UNION ALL
SELECT '10_sensitivity_include_massive_transfusion', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
WHERE eligible_include_massive_transfusion_sensitivity = 1
```

- [ ] **Step 5: Run the SQL contract tests**

Run:

```bash
python3 -m unittest \
  tests.test_massive_transfusion_sensitivity_contract.SqlContractTests -v
```

Expected: all three SQL contract tests pass.

- [ ] **Step 6: Review the SQL diff and commit**

Run:

```bash
git diff --check
git diff -- 10_create_non_traumatic_sah_cohort.sql
```

Expected: no whitespace errors; the primary CASE remains byte-for-byte equivalent in eligibility logic, and the new CASE contains only the missingness condition.

```bash
git add 10_create_non_traumatic_sah_cohort.sql
git commit -m "Expose the inclusive transfusion sensitivity cohort"
```

### Task 3: Route the new cohort through the existing Python sensitivity pathway

**Files:**
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:164-168`
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:252-255`
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:353-355`
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:330-385`
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:1174-1182`
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:1627-1697`
- Test: `tests/test_massive_transfusion_sensitivity_contract.py`

**Interfaces:**
- Consumes: `eligible_include_massive_transfusion_sensitivity` from `physiology_features_48h`.
- Produces: sensitivity registry entry named `include_massive_transfusion`, an `ANALYSIS_SUPERSET_FLAG`, a primary-only dataframe for existing workflows, and an unfiltered superset for cohort sensitivity; preserves primary `COHORT_FLAG`.

- [ ] **Step 1: Extend the Python contract test for the loader/filter interaction**

Append the following assertions to `test_python_loads_and_registers_sensitivity_flag`:

```python
        self.assertIn(
            'ANALYSIS_SUPERSET_FLAG = "eligible_include_massive_transfusion_sensitivity"',
            self.source,
        )
        self.assertIn("WHERE {ANALYSIS_SUPERSET_FLAG} = 1", self.source)
        self.assertIn("analysis_df = read_table_from_bigquery()", self.source)
        self.assertIn(
            "df = analysis_df[analysis_df[COHORT_FLAG] == 1].copy()",
            self.source,
        )
        self.assertRegex(
            self.source,
            r'run_sensitivity_cohort_summaries\(\s*analysis_df,\s*primary\["assignments"\]\s*,?\s*\)',
        )
```

- [ ] **Step 2: Run the focused test and verify RED**

```bash
python3 -m unittest \
  tests.test_massive_transfusion_sensitivity_contract.PythonContractTests -v
```

Expected: FAIL because `ANALYSIS_SUPERSET_FLAG` and the split primary/superset data flow are not implemented.

- [ ] **Step 3: Document both cohort flags in configuration**

Keep the existing cohort comments, add the inclusive comment, and define the two roles exactly:

```python
#   eligible_include_massive_transfusion_sensitivity: 不排除 0-24h 大量输血
COHORT_FLAG = "eligible_primary_analysis"
ANALYSIS_SUPERSET_FLAG = "eligible_include_massive_transfusion_sensitivity"
```

- [ ] **Step 4: Register the sensitivity cohort**

Make the registry exactly:

```python
SENSITIVITY_COHORT_FLAGS = {
    "no_rbc_48h": "eligible_no_transfusion_sensitivity",
    "icu_los_ge_48h": "eligible_sensitivity_48h_los",
    "include_massive_transfusion": "eligible_include_massive_transfusion_sensitivity",
}
```

- [ ] **Step 5: Load the new field from BigQuery**

Add this string after the other eligibility flags in `selected_columns`:

```python
"eligible_include_massive_transfusion_sensitivity",
```

- [ ] **Step 6: Query the analysis superset instead of the primary subset**

Change the loader docstring, query predicate, and status print to:

```python
def read_table_from_bigquery() -> pd.DataFrame:
    """从 BigQuery 读取覆盖主分析及队列敏感性分析的最小宽表超集。"""
```

```python
    WHERE {ANALYSIS_SUPERSET_FLAG} = 1
```

```python
    print(f"读取 cohort superset flag：{ANALYSIS_SUPERSET_FLAG} = 1")
```

- [ ] **Step 7: Derive the primary dataframe and preserve sensitivity access to the superset**

Start the main flow exactly as follows:

```python
analysis_df = read_table_from_bigquery()
df = analysis_df[analysis_df[COHORT_FLAG] == 1].copy()
validate_input(df)
```

Keep every existing primary analysis call on `df`. Change only the cohort-sensitivity call to:

```python
sensitivity_cohort_summary = run_sensitivity_cohort_summaries(
    analysis_df,
    primary["assignments"],
)
```

Change that function's docstring to:

```python
"""在覆盖预定义队列的宽表超集中分别重新聚类并汇总结局。"""
```

- [ ] **Step 8: Run contract and syntax checks**

Run:

```bash
python3 -m unittest \
  tests.test_massive_transfusion_sensitivity_contract.PythonContractTests -v
python3 -m py_compile 11_bigquery_notebook_non_traumatic_sah_analysis.py
```

Expected: the Python contract test passes and `py_compile` exits 0 without output.

- [ ] **Step 9: Review and commit**

```bash
git diff --check
git diff -- 11_bigquery_notebook_non_traumatic_sah_analysis.py
git add 11_bigquery_notebook_non_traumatic_sah_analysis.py \
  tests/test_massive_transfusion_sensitivity_contract.py
git commit -m "Run the inclusive transfusion sensitivity analysis"
```

### Task 4: Align protocol, SAP, and the append-only deviation record

**Files:**
- Create from pinned source then modify: `protocol.md`
- Create from pinned source then modify: `sap.md`
- Create: `deviations.md`
- Test: `tests/test_massive_transfusion_sensitivity_contract.py`

**Interfaces:**
- Consumes: approved design, implemented SQL/Python names, and the read-only source documents.
- Produces: version `0.1.1` governance documents that remain `DRAFT_BLOCKED`, plus deviation ID `DEV-2026-07-16-001`.

- [ ] **Step 1: Verify and bring the source documents into the active worktree**

Verify the read-only inputs before creating the worktree copies:

```bash
shasum -a 256 \
  /Users/fang/code/mimic_asah_study/protocol.md \
  /Users/fang/code/mimic_asah_study/sap.md
```

Expected:

```text
fe931d178e738e5b72dbf9c5d4e6e975a4009da68fe7d3499bd41cb83327815e  /Users/fang/code/mimic_asah_study/protocol.md
a8ea4fcc7c5fd73eb4af48f17628730ceaa582d7cac8230c91be28ddc3df5898  /Users/fang/code/mimic_asah_study/sap.md
```

Use `apply_patch` to create `protocol.md` and `sap.md` as verbatim copies of those pinned inputs. Before making the substantive edits, verify the worktree copies have the same two hashes.

- [ ] **Step 2: Update the protocol cohort decision and version**

Set YAML `version: "0.1.1"`, retaining `status: DRAFT`, `freeze_decision: DRAFT_BLOCKED`, and `outcome_access_before_freeze: "accessed"`.

Replace Section 6.2 with:

```markdown
### 6.2 主分析大量输血排除与敏感性人群

主分析继续排除 ICU 入科后 0–24h `massive_transfusion_24h = 1`；其操作定义为 RBC 事件数 ≥5 或可换算单位总量 ≥5。因此，主分析的描述性目标人群限于未观察到上述早期大量 RBC 输血的患者。该条件发生在 cohort entry 之后，可能反映早期治疗与病情严重度并造成治疗相关选择，不能解释为疾病固有入组条件。

支持性敏感性分析使用 `eligible_include_massive_transfusion_sensitivity = 1`，仅移除大量输血限制，仍要求八项核心变量缺失数 ≤2，并保持其他队列规则、时间窗口、特征和结局定义不变。比较样本量、cluster size、表型中心/特征谱和结局关联方向；若结构明显改变，应报告治疗敏感性并限制表型的本质化命名。该决定形成于结局已访问之后，属于探索性固定，不得描述为结果揭盲前预设，也不用于估计 RBC 输血的因果效应。
```

Change the massive-transfusion blocker at the current Section 13 checklist to:

```markdown
- [x] 已确认 post-entry 大量输血排除的目标人群含义并在 SQL/Python 中增加不排除敏感性分析；决定时结局已访问，详见 `deviations.md#dev-2026-07-16-001`。
```

Append this version row:

```markdown
| 0.1.1 | 2026-07-16 | DRAFT_BLOCKED | 固定主分析大量输血排除的目标人群解释，增加不排除大量输血敏感性分析，并保留结果已访问后的探索性边界。 |
```

- [ ] **Step 3: Update the SAP implementation contract and version**

Set YAML `sap_version: "0.1.1"` and `protocol_version: "0.1.1"`, retaining all status and outcome-access fields.

Replace cohort-flow items 8–9 with:

```markdown
8. 主分析排除 0–24h 大量输血；
9. 不排除大量输血敏感性人群；
10. 其他敏感性人群。
```

Immediately after the sensitivity matrix add:

```markdown
### 13.1 不排除大量输血敏感性分析契约

`eligible_include_massive_transfusion_sensitivity = 1` 定义为八项核心变量缺失数 ≤2，不限制 `massive_transfusion_24h`。该版本只移除大量输血限制；预处理、主 7 变量、K=3、随机种子和结局定义与主分析保持一致，并在该敏感性样本内独立拟合插补、标准化、PCA 和 K-means。

该分析为支持性而非共同主要分析。比较样本量、cluster size、表型中心/特征谱和结局关联方向，不按结果选择优先版本。若差异明显，结论应表述为表型结构对早期治疗敏感，并限制本质化命名；不得据此估计 RBC 输血因果效应。该规则在结局已访问后固定，不得描述为结果揭盲前预设。
```

Add this implementation-status row to Section 16:

```markdown
| Post-entry 大量输血排除 | 主分析保留排除；已增加 `eligible_include_massive_transfusion_sensitivity` 并接入 Python 敏感性流程 | 已实现；维持探索性解释并保留 deviation 记录 |
```

Append this version row:

```markdown
| 0.1.1 | 2026-07-16 | DRAFT_BLOCKED | 固定大量输血主/敏感性人群契约并记录结果已访问后的探索性实施；其他冻结阻塞项保持开放。 |
```

- [ ] **Step 4: Create the append-only deviation record**

Create `deviations.md` exactly as follows:

````markdown
# Analysis Deviations Log

本文件为追加式记录。既有条目不得静默改写；如需更正，应新增带日期的勘误条目并引用原 deviation ID。

## DEV-2026-07-16-001

```yaml
date: "2026-07-16"
study_id: "MIMIC-NSAH-PHENO-01"
protocol_version: "0.1.1"
sap_version: "0.1.1"
status: "implemented_exploratory"
outcome_access_before_decision: "accessed"
affected_files:
  - "10_create_non_traumatic_sah_cohort.sql"
  - "11_bigquery_notebook_non_traumatic_sah_analysis.py"
  - "protocol.md"
  - "sap.md"
```

### 变更

保留主分析对 ICU 入科后 0–24h 大量 RBC 输血的排除，并新增 `eligible_include_massive_transfusion_sensitivity`。新敏感性人群仅移除大量输血限制，其他队列、缺失阈值、特征、时间窗口和结局定义保持不变。

### 理由

大量输血标志发生在 cohort entry 之后，可能反映早期治疗和严重度并造成选择。全纳入敏感性分析用于评估表型结构和结局关联是否依赖该排除，同时保持当前主分析与稿件人群的连续性。

### 时间与解释边界

该决定形成时既有分析结果和结局已经访问，因此不得描述为结果揭盲前预设，也不能恢复前瞻性冻结状态。该分析仅为探索性稳健性评估，不估计 RBC 输血的因果效应。`protocol.md` 和 `sap.md` 继续保持 `DRAFT_BLOCKED`，其他冻结阻塞项不受本条影响。

### 验证范围

仅完成静态合同测试、Python 语法检查和差异审查；未执行 BigQuery，未重建结果表，未访问或导出患者级数据。
````

- [ ] **Step 5: Run governance contract tests and boundary searches**

Run:

```bash
python3 -m unittest \
  tests.test_massive_transfusion_sensitivity_contract.GovernanceContractTests -v
rg -n "freeze_decision: DRAFT_BLOCKED|outcome_access_before_freeze: \"accessed\"|eligible_include_massive_transfusion_sensitivity|不得描述为结果揭盲前预设" \
  protocol.md sap.md deviations.md
```

Expected: the governance test passes; each required boundary is visible in the relevant documents.

- [ ] **Step 6: Review and commit the governance documents**

```bash
git diff --check
git diff -- protocol.md sap.md deviations.md
git add protocol.md sap.md deviations.md
git commit -m "Document the outcome-informed transfusion sensitivity decision"
```

### Task 5: Run final static verification and review the complete change

**Files:**
- Verify: `10_create_non_traumatic_sah_cohort.sql`
- Verify: `11_bigquery_notebook_non_traumatic_sah_analysis.py`
- Verify: `protocol.md`
- Verify: `sap.md`
- Verify: `deviations.md`
- Verify: `tests/test_massive_transfusion_sensitivity_contract.py`

**Interfaces:**
- Consumes: all Task 1–4 deliverables.
- Produces: evidence that the approved cross-file contract is implemented without claiming result-level validation.

- [ ] **Step 1: Run the complete regression contract**

```bash
python3 -m unittest tests/test_massive_transfusion_sensitivity_contract.py -v
```

Expected: five tests pass with final status `OK`.

- [ ] **Step 2: Run Python syntax validation**

```bash
python3 -m py_compile \
  11_bigquery_notebook_non_traumatic_sah_analysis.py \
  tests/test_massive_transfusion_sensitivity_contract.py
```

Expected: exit status 0 with no output.

- [ ] **Step 3: Confirm flag propagation and primary-cohort preservation**

```bash
rg -n "eligible_primary_analysis|eligible_include_massive_transfusion_sensitivity|include_massive_transfusion" \
  10_create_non_traumatic_sah_cohort.sql \
  11_bigquery_notebook_non_traumatic_sah_analysis.py \
  protocol.md sap.md deviations.md \
  tests/test_massive_transfusion_sensitivity_contract.py
```

Expected: the primary flag still contains `massive_transfusion_24h = 0`; the inclusive flag is defined in SQL, counted twice, placed in the flowchart, selected and registered in Python, and documented in all three governance files.

- [ ] **Step 4: Review repository state and commit any test-only corrections**

```bash
git diff --check
git status --short
git log --oneline -6
```

Expected: no uncommitted task files, no accidentally staged `.superpowers/`, and separate commits for the contract test, SQL, Python, and governance documents. If verification required a test-only correction, commit only that correction with a Lore-formatted message and record the exact checks run.

- [ ] **Step 5: Report verification boundaries**

The handoff must explicitly state:

```text
Static contract and Python syntax checks passed.
BigQuery was not executed; no result-level sensitivity estimates were regenerated.
Protocol and SAP remain DRAFT_BLOCKED because unrelated freeze blockers remain open.
```

### Task 6: Resolve final whole-branch review findings

**Files:**
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:28`
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:1175-1236`
- Modify: `11_bigquery_notebook_non_traumatic_sah_analysis.py:1754`
- Modify: `tests/test_massive_transfusion_sensitivity_contract.py`
- Modify: `protocol.md`
- Modify: `sap.md`
- Modify: `deviations.md`

**Interfaces:**
- Consumes: the inclusive superset, primary assignments, seven `FEATURES`, and per-sensitivity refitted scaled K-means solution.
- Produces: actual sensitivity flag metadata, `primary_overlap_n`, overlap-based `ari_vs_primary_subset`, seven `<feature>_mean` values, seven `<feature>_standardized_center` values, and governance version `0.1.2`.

- [ ] **Step 1: Add a synthetic behavioral regression test**

Create a deterministic synthetic dataframe with at least 60 stays in three separated clusters, including primary-overlap stays and added stays eligible only for `eligible_include_massive_transfusion_sensitivity`. Exercise the actual `run_sensitivity_cohort_summaries` function using the script's production helper functions and assert:

```python
self.assertEqual(set(result["cohort_flag"]), {"eligible_include_massive_transfusion_sensitivity"})
self.assertEqual(set(result["primary_overlap_n"]), {len(primary_assignments)})
self.assertTrue(result["ari_vs_primary_subset"].notna().all())
for feature in features:
    self.assertTrue(result[f"{feature}_mean"].notna().all())
    self.assertTrue(result[f"{feature}_standardized_center"].notna().all())
```

The test must load the production function and helpers without executing the notebook's BigQuery client or main flow. Run it before implementation and record the expected RED caused by missing metadata/profile behavior.

- [ ] **Step 2: Correct sensitivity summary metadata and overlap ARI**

For every sensitivity result row set:

```python
"cohort_flag": flag_col
```

After merging primary labels, define the overlap and ARI as:

```python
overlap = assignments.dropna(subset=["primary_phenotype"])
ari = (
    adjusted_rand_score(
        overlap["primary_phenotype"].astype(int),
        overlap["phenotype"].astype(int),
    )
    if len(overlap) >= 2
    else np.nan
)
```

Add `primary_overlap_n = int(len(overlap))` to every non-small result row. For the too-small branch, add `primary_overlap_n` using the intersection of `sub_df.stay_id` with primary assignment stay IDs and keep ARI/profile values missing with the existing explanatory note.

- [ ] **Step 3: Persist raw profiles and standardized centers**

Retain the centers returned by `build_ordered_phenotype_labels`. For each phenotype row add, for every feature in `FEATURES`:

```python
row[f"{feature}_mean"] = float(group[feature].mean())
row[f"{feature}_standardized_center"] = float(
    centers.loc[centers["phenotype"] == phenotype, feature].iloc[0]
)
```

Do not introduce PCA, change `FEATURES`, or change clustering parameters.

- [ ] **Step 4: Align user-facing Python documentation**

Update the output inventory and final console guidance so `phenotype_sensitivity_cohort_summary` names all three cohorts: no RBC, ICU LOS ≥48h, and inclusion of massive transfusion. State that the table includes overlap ARI and feature profiles/centers.

- [ ] **Step 5: Correct protocol/SAP to the implemented seven-feature direct K-means pipeline**

Bump protocol/SAP to `0.1.2`. Replace implemented-pipeline references to eight features and PCA with:

```text
seven core features; median imputation; Z-score standardization; direct K-means in seven-dimensional scaled space
```

This includes YAML metadata, cohort missingness rules, preprocessing/algorithm descriptions, phenotype profiles, frozen-transport parameter lists, the massive-transfusion subsection, and implementation-difference language. Preserve `DRAFT_BLOCKED`, prior outcome access, and unrelated blockers. Remove `deviations.md` from protocol line 50's list of still-missing artifacts because the file now exists.

The massive-transfusion subsection must state that preprocessing independently refits median imputation, standardization, and direct K-means with no PCA. Its interpretation criteria must name sample size, cluster size, raw feature profiles, standardized centers, overlap ARI, and outcome-association direction.

- [ ] **Step 6: Append a second deviation entry**

Append `DEV-2026-07-16-002` without rewriting `DEV-2026-07-16-001`. Record versions `0.1.2`, prior outcome access, correction of the seven-feature/no-PCA description, addition of overlap ARI and persisted profiles/centers, continued exploratory/non-causal status, and no BigQuery execution.

- [ ] **Step 7: Strengthen governance/static assertions**

Require protocol/SAP version `0.1.2`, seven-feature/direct-K-means wording, absence of PCA in the massive-transfusion subsection, `DEV-2026-07-16-002`, actual sensitivity cohort metadata, `primary_overlap_n`, and profile/center field construction.

- [ ] **Step 8: Run focused and full verification**

```bash
python3 -m unittest tests/test_massive_transfusion_sensitivity_contract.py -v
python3 -m py_compile \
  11_bigquery_notebook_non_traumatic_sah_analysis.py \
  tests/test_massive_transfusion_sensitivity_contract.py
git diff --check
```

Expected: all tests pass, both Python files compile without output, and no whitespace errors are reported. BigQuery remains unexecuted.

- [ ] **Step 9: Commit the final-review fixes**

```bash
git add 11_bigquery_notebook_non_traumatic_sah_analysis.py \
  tests/test_massive_transfusion_sensitivity_contract.py \
  protocol.md sap.md deviations.md
git commit -m "Make sensitivity robustness outputs match their governance contract"
```
