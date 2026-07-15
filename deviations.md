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
