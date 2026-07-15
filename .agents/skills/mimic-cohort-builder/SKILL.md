---
name: mimic-cohort-builder
description: Build and review MIMIC-IV clinical cohorts with BigQuery SQL. Use for inclusion/exclusion criteria, ICD diagnosis/procedure evidence, first ICU stay selection, T0/index-time definitions, adult filters, cohort audit tables, row-count checks, and avoiding join duplication or time-window leakage.
---

# MIMIC Cohort Builder

用这个 skill 构建或审查 MIMIC-IV cohort。目标是让 cohort definition 可复现、可审计、时间顺序正确，并且不会因为 join 粒度错误而静默膨胀样本。

读取患者级数据或执行查询前，先应用 `mimic-data-governance`。如果无法确认本地或云端环境满足 DUA、zero retention、no training 和 no human review 要求，只审查 SQL 文本和非敏感 schema，不读取受限结果。

## 先固定研究设计

- 明确研究对象：疾病/综合征、住院患者还是 ICU 患者、成人定义、是否只取 first ICU stay。
- 不要让一个 `T0` 同时表示多个时间概念。按研究需要分别定义 `eligibility_time`、`cohort_entry_time`、`index_time`、`prediction_landmark`、`treatment_assignment_time`、`followup_start`、`censoring_time` 和 `outcome_time`。
- 明确分析粒度：patient-level (`subject_id`)、admission-level (`hadm_id`) 或 ICU stay-level (`stay_id`)。
- 明确源数据版本：默认 MIMIC-IV 3.1，除非用户或仓库另有说明。
- 明确目标 project/dataset：优先使用用户本轮指定，其次读取当前仓库约定；不清楚时用 `<PROJECT_ID>.<DATASET>` 占位。

## 推荐构建顺序

1. 建立候选诊断/操作证据表。
2. 连接 `hosp.admissions` 和 `hosp.patients`，加入年龄、入院/出院、死亡、基本人口学。
3. 连接 `icu.icustays`，限定 ICU 住院记录。
4. 应用 inclusion/exclusion criteria。
5. 排序选择 first ICU stay 或 first admission，并保留选择理由。
6. 派生适用的命名时间、follow-up boundaries 和主要 outcome flags。
7. 输出 cohort audit：每一步人数、住院数、ICU stay 数、排除原因。

年龄必须依据 `anchor_age`、`anchor_year` 和事件年份计算并记录规则。明确高龄去标识化/顶格处理的解释限制，不要把 anchor 信息当成未经处理的真实出生日期。

## ICD 与代码证据

- MIMIC-IV 的 `icd_code` 去除了小数点，例如 `I60.9` 存为 `I609`。
- 使用 `icd_version` 显式区分 ICD-9 与 ICD-10。
- 匹配子类时优先使用明确前缀，例如 `icd_code LIKE 'I60%'`。
- 保留 code list CTE 或 code table，并输出 matched `long_title` 方便审计。
- 排除诊断要和纳入诊断一样可审计，不要只在 `WHERE NOT` 中隐式处理。

## Join 规则

- `subject_id`：患者。
- `hadm_id`：住院。
- `stay_id`：ICU stay。
- 不要使用 MIMIC-III 的 `icustay_id`。
- 连接 ICU 表时保留 `subject_id`、`hadm_id`、`stay_id` 三个键，用来检查一致性。
- 对 event-level 表先聚合到目标粒度，再回连 cohort，避免 many-to-many join。

## 时间窗与泄漏

- baseline covariates 必须发生在其对应的 decision 或 treatment-assignment time 之前；ICU 入科后的早期变量不能笼统称为入科前 baseline。
- exposure window 必须相对 `treatment_assignment_time` 或 `index_time` 写成明确区间。
- outcome 必须从统一 `followup_start` 后观察。
- 对 `0-24h` 特征预测，使用 24h landmark 并定义仍在风险集的人群，或采用有效动态设计。
- 优先使用半开区间，避免边界重复计数。
- BigQuery 中注意 `TIMESTAMP` 和 `DATETIME` 类型差异，比较或 `TIMESTAMP_DIFF` 前要显式转换。

## 审计输出

每个 cohort SQL 至少应能回答：

- 初始候选患者数、住院数、ICU stay 数是多少？
- 每个排除条件剔除了多少？
- 最终 cohort 是否有重复 `subject_id`、`hadm_id` 或 `stay_id`？
- first stay 选择是否可复现？
- 诊断/操作 code match 的描述是否可查看？
- 所有命名时间是否落在 admission/ICU stay 合理范围内，且顺序与设计一致？

## 完成前检查

- 完整 BigQuery 表名使用反引号。
- 版本、project、dataset 与当前任务一致。
- 每个 inclusion/exclusion 都有注释或可审计中间表。
- event-level 表没有直接 many-to-many 回连最终 cohort。
- SQL 至少做 syntax-level 检查；有权限时运行 dry run 或 row-count query。
