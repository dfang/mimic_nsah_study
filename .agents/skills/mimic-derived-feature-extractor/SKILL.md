---
name: mimic-derived-feature-extractor
description: Extract early physiologic and laboratory features from MIMIC-IV derived tables. Use for 0-24h/0-48h ICU features, baseline/lookback windows, vitals, GCS, blood gas, chemistry, CBC, coagulation, urine output, ventilation, missingness flags, clinical range filters, and feature naming conventions.
---

# MIMIC Derived Feature Extractor

用这个 skill 从 MIMIC-IV `derived` tables 抽取早期生理、实验室和 ICU 支持治疗特征。优先使用社区 derived concepts，只有缺失或需要审计 item-level 证据时才回退 raw event tables。

读取查询结果前先应用 `mimic-data-governance`。外部 AI 服务未验证 zero retention、no training 和 no human review 时，不要传输患者级特征、临床文本或敏感衍生数据。

## 默认表优先级

- 生命体征：`derived.vitalsign`
- 神经状态：`derived.gcs`
- 血气：`derived.bg`
- 生化：`derived.chemistry`
- 血常规：`derived.complete_blood_count`
- 凝血：`derived.coagulation`
- 尿量：`derived.urine_output`
- 呼吸支持：`derived.ventilation`、`derived.oxygen_delivery`
- ICU stay 明细：`derived.icustay_detail`
- 严重程度评分：`derived.apsiii`、`derived.oasis`、`derived.sofa`，前提是当前 mirror 中存在。

如果 derived table 不确定，先检查 metadata，不要凭记忆硬写。

先发现并使用用户实际可见的 derived schema；支持 `physionet-data.mimiciv_3_1_derived` 这类 versioned schema 和 `physionet-data.mimiciv_derived` 这类 alias。先用 `INFORMATION_SCHEMA.TABLES` 判断 `_metadata` 是否存在；存在时记录 MIMIC 版本、mimic-code 版本和 commit，不存在时记录该检查及等价构建来源，不要直接生成必然失败的 `_metadata` 查询。不要仅凭命名惯例覆盖用户已验证的 schema。

## 时间窗设计

- ICU 早期窗口通常以 `cohort_entry_time = icustays.intime` 对齐，但这不自动等于 prediction landmark 或 treatment assignment time。
- 常见窗口：`0-24h`、`0-48h`。
- lab lookback 必须单独命名，例如 `hemoglobin_min_m6_24h` 表示 `-6h to +24h`。
- 不要把 pre-ICU baseline 和 post-ICU early physiology 混成一个变量，除非方案明确允许。
- 如果这些特征用于预测，`prediction_landmark` 必须位于特征窗口结束之后，并定义该时点仍在风险集的人群。
- 如果这些特征用于因果调整，只允许使用 treatment assignment 前的值；不要把 post-treatment 变量当 confounder。
- 使用半开区间，避免边界重复计数。

## 聚合模式

连续变量常用：

- `min`
- `max`
- `avg` 或 median/quantile，如果实现可靠
- `first` 和 `last`，需用 `ARRAY_AGG(... ORDER BY charttime)` 或窗口函数
- `count`
- `missing_flag`

分类/状态变量常用：

- ever/any flag
- dominant state
- first state
- duration 或 hours exposed

## 命名规范

- 格式：`<concept>_<summary>_<window>`。
- 示例：`heart_rate_max_0_48h`、`gcs_min_0_24h`、`hemoglobin_first_m6_24h`。
- 保留单位含义，必要时在 data dictionary 或注释中说明。
- 不要用含糊列名，例如 `lab1`、`score_final`、`feature_a`。

## 范围过滤

- 聚合前应用 clinically plausible range filters。
- 范围应保守，避免把真实极端值误删。
- 对每个被过滤变量写 SQL 注释，说明单位和过滤边界。
- 如果某变量单位可能混杂，先核查单位或来源，不要直接聚合。

## 缺失处理

- 在特征表中保留 `*_missing` 或 `*_count`，让建模阶段知道测量频率和缺失模式。
- 不要在 SQL 抽取阶段默认均值填补，除非这是明确的分析方案。
- 对 GCS、通气、镇静、插管相关缺失要谨慎解释。

## 回退 raw tables 的条件

只有在以下情况使用 `icu.chartevents`、`hosp.labevents` 等 raw tables：

- derived table 不存在。
- derived concept 缺少研究所需变量。
- 需要 item-level 审计或复现。
- 需要验证 derived concept 的覆盖情况。

使用 raw `chartevents` 时必须尽早用 cohort `stay_id` 和 `itemid` 过滤，避免全表 join。
