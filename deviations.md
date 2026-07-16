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

## DEV-2026-07-16-002

```yaml
date: "2026-07-16"
study_id: "MIMIC-NSAH-PHENO-01"
protocol_version: "0.1.2"
sap_version: "0.1.2"
status: "implemented_exploratory"
outcome_access_before_decision: "accessed"
supersedes_description_in: "DEV-2026-07-16-001"
affected_files:
  - "11_bigquery_notebook_non_traumatic_sah_analysis.py"
  - "protocol.md"
  - "sap.md"
```

### 更正与新增输出

更正 0.1.1 文档中对已实现表型流程的描述：当前主分析和不排除大量输血敏感性分析均使用七项核心特征、中位数插补、Z-score 标准化，并在七维标准化空间直接运行 K-means；已实现流程不包含 PCA。该更正不改变主队列、七项 `FEATURES`、K=3、随机种子、估计器或结局定义。

敏感性汇总新增实际 cohort flag、与主分析重叠 stay 数、仅在重叠 stays 上计算的 ARI，以及每个敏感性表型的七项原始特征均值和标准化中心。这些字段用于评估样本变化、表型结构和特征谱是否稳健。

### 时间与解释边界

本次更正和输出扩展发生在结局已访问后，继续属于探索性、非因果性分析，不得描述为结果揭盲前预设，不改变 `DRAFT_BLOCKED` 状态，也不支持估计 RBC 输血的因果效应。`DEV-2026-07-16-001` 保持原文，本文作为追加式勘误记录。

### 验证范围

仅使用合成数据完成行为回归测试，并完成静态合同测试、Python 语法检查和差异审查；未执行 BigQuery，未重建真实结果表，未访问或导出患者级数据。
