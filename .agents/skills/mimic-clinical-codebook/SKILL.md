---
name: mimic-clinical-codebook
description: Create and audit clinical codebooks for MIMIC-IV studies. Use for ICD-9/ICD-10 diagnosis and procedure code lists, d_items and d_labitems itemid searches, medication/lab/procedure concept mapping, inclusion/exclusion code evidence, and matched-description audit tables.
---

# MIMIC Clinical Codebook

用这个 skill 为 MIMIC-IV 研究建立可审计 codebook。重点是让 disease definitions、procedure evidence、itemid concepts 和 medication/lab concepts 可复查、可扩展、可解释。

读取患者级命中结果前先应用 `mimic-data-governance`。优先使用字典表、代码描述和非敏感汇总审计概念；不要把受限明细发送到未验证的外部服务。

## 适用场景

- 构建疾病诊断 code list。
- 构建排除诊断 code list。
- 构建手术/操作 evidence。
- 搜索 `d_items` 或 `d_labitems` 的 `itemid`。
- 审查已有 SQL 的 ICD/itemid 匹配是否漏掉同义词或子类。
- 为 manuscript supplement 输出 code definitions。

## ICD 规则

- MIMIC-IV `icd_code` 不含小数点。
- ICD-9 和 ICD-10 必须用 `icd_version` 分开处理。
- 使用 `d_icd_diagnoses.long_title` 或 `d_icd_procedures.long_title` 审计匹配结果。
- 对宽泛前缀匹配要检查误纳入风险。
- 对排除条件也要保留 matched descriptions，不要只保留逻辑表达式。

## Itemid 搜索规则

- 搜索 `icu.d_items` 时，同时查看 `label`、`category`、`unitname`、`linksto`。
- 搜索 `hosp.d_labitems` 时，同时查看 `label`、`fluid`、`category`。
- 关键词要覆盖同义词、缩写、大小写差异。
- 对高风险概念，输出候选 itemid 列表后再人工/临床审查。
- 不要把 MIMIC-III itemid 直接迁移到 MIMIC-IV，必须重新核查。

## Medication 与 Procedure 概念

- 用药概念可来自 `prescriptions`、`pharmacy`、`emar`、`emar_detail`，先明确研究需要的是 order 还是 administration。
- ICU medication/fluid 可来自 `icu.inputevents`，重点核查 `itemid`、`label`、`amount`、`amountuom`、`rate`。
- procedure evidence 可来自 ICD procedures、`icu.procedureevents`，或两者组合。

## 推荐输出

Codebook 至少包含：

- `concept_name`
- `source_table`
- `code_system` 或 `itemid`
- `code`
- `icd_version`
- `matched_label`
- `include_or_exclude`
- `notes`
- `source_version`
- `query_or_rule_hash`
- `reviewer`
- `freeze_status`

## 审查清单

- code list 是否覆盖 ICD-9 与 ICD-10？
- 是否处理了去小数点格式？
- 是否保留 matched descriptions？
- 是否区分 diagnosis evidence 与 procedure evidence？
- 是否区分 order 与 administration？
- 是否明确排除条件的临床含义？
- 下游 cohort 是否引用同一个冻结 codebook，变更是否写入 deviation log？
