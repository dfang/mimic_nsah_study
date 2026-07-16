# Study Protocol

## Early Multimodal Physiological Phenotypes and Outcomes in Critically Ill Adults With Non-traumatic Subarachnoid Hemorrhage

```yaml
study_id: "MIMIC-NSAH-PHENO-01"
title: "Early Multimodal Physiological Phenotypes and Outcomes in Critically Ill Adults With Non-traumatic Subarachnoid Hemorrhage"
version: "1.0.0"
status: FROZEN_EXPLORATORY
freeze_decision: FROZEN_2026-07-16
design_family: "phenotyping"
design_subtype: "not_applicable"
association_intent: "not_applicable"
modalities: ["structured"]
validation_role: "development"
confirmatory_status: "exploratory"
clinical_question: "在入住 ICU 的成年非创伤性蛛网膜下腔出血患者中，ICU 入科后 0–48 小时的八项常规生理指标能否形成稳定、可解释的多模态生理表型，以及这些表型与院内死亡和早期贫血负担有何非因果性关联？"
clinical_decision_context: "用于病理生理描述、风险富集和后续前瞻性验证假设生成；不是床旁实时诊断、治疗分配工具或已验证的预后模型。"
data_sources_ref: "reproducibility/run-manifest.yaml#data_sources"
governance_decision_ref: "#data-governance"
analysis_grain:
  unit: "stay"
  key_columns: ["subject_id", "hadm_id", "stay_id"]
  repeat_structure: "每次符合条件的住院保留首次 ICU stay；同一 subject_id 可贡献多次住院，所有 bootstrap 和交叉验证以 subject_id 为分组单位。"
estimand_or_target:
  population: "MIMIC-IV 3.1 中入住 ICU 的成年 non-traumatic SAH 患者"
  strategies_or_predictors: "ICU 入科后 [0,48h) 八项早期生理特征形成的 log1p + 标准化 + PCA + K-means 表型空间"
  comparator: "表型间比较；有序标签 P1 为生理严重度最低的参考表型"
  outcome: "主要外部判据为院内死亡；表型发现本身不使用结局"
  horizon: "同次住院全程；院内死亡仅作为可能与 0-48h 特征窗口重叠的描述性外部判据"
  intercurrent_events: "48h 前死亡、出院和治疗均保留在描述性目标中；不得解释为 48h 后预测或因果效应"
  summary_measure: "表型规模、原始/标准化中心、稳定性、表型与院内死亡的 OR 及 95% CI"
  contrast: "P2 vs P1、P3 vs P1；仅解释为关联，不解释为治疗效应或病因效应"
dag_ref: null
timeline_ref: "#timeline-contract"
primary_outcome: "院内全因死亡（hospital_expire_flag），作为同次住院描述性外部判据而非 landmark 后结局"
secondary_outcomes: ["ICU 死亡", "ICU 住院时长", "住院时长", "独立严重程度评分梯度"]
reporting_guidelines: ["STROBE cohort", "RECORD"]
preregistration:
  registry: null
  identifier: null
  registered_at: null
outcome_access_before_freeze: "accessed"
```

## 1. 文档定位和版本声明

本文件是根据当前仓库中的队列 SQL、分析代码和研究策略，于既有分析结果已被查看后形成的重建性研究方案。它不能被描述为前瞻性注册或结果揭盲前冻结的 protocol。所有从既有结果或既有稿件中形成的分析选择均归为探索性；若未来需要确认性检验，应使用独立数据、明确的再验证阶段或新版本 protocol/SAP。

版本 1.0.0 在授权环境完成 MIMIC-IV/eICU 全流程重跑、聚合 QC、结果复核和披露抑制后冻结。该冻结仅表示分析定义、代码、结果和解释边界不可再无版本修改；由于方案形成于结果访问后，仍为回顾性探索性冻结，不构成前瞻性预注册或确认性分析。

## 2. Data governance

```yaml
governance_decision: PROCEED_LOCAL
scope: "授权本地 BigQuery 执行、统计重跑、聚合 QC、结果对账和冻结元数据；不持久化或提交患者级行。"
data_classes: ["PUBLIC", "MIMIC_RESTRICTED", "DERIVED_SENSITIVE", "AGGREGATE_REVIEW"]
source_projects_and_versions:
  - "MIMIC-IV 3.1"
  - "eICU-CRD 2.0"
authorized_user_confirmed: true
processing_destinations: ["local workspace"]
service_evidence:
  zero_retention: unknown
  no_training: unknown
  no_human_review: unknown
  subprocessors_and_region: unknown
  verified_on: null
controls:
  - "患者级数据仅在授权 BigQuery/进程内计算，不打印、不本地持久化、不提交"
  - "不把去标识化 MIMIC 数据视为公开数据"
  - "仓库仅保留经复核的聚合结果、代码、文档和非敏感 job provenance"
  - "公开产物中非零小单元格 <10 已抑制；结果不得据此提升为确认性"
excluded_paths:
  - ".git/"
  - ".env* and credentials"
  - "patient-level exports and data directories"
  - "notebook outputs, logs, caches, model artifacts"
  - "undisclosed aggregate result artifacts"
release_plan: "代码与文档可在清除内联真实值/凭据后审查发布；汇总结果需单独披露审查；衍生数据和模型默认敏感。"
blockers:
  - "公开投稿前仍需作者/机构完成最终披露审批；本冻结仅完成本地保守抑制审查"
next_review_date: null
```

任何后续读取真实 MIMIC 数据、查询结果或衍生患者级表的步骤，必须在获授权研究者控制的合规环境中重新运行治理门禁。

## 3. 研究目标

### 3.1 主要目标

在符合条件的 non-traumatic SAH ICU stays 中，基于结局盲态的八维早期生理输入空间识别 K=3 生理表型，并评估表型的规模、分离度、重采样稳定性和临床可解释性。

### 3.2 次要目标

1. 描述各表型的院内死亡、ICU 死亡、早期贫血、RBC 输血、资源使用和常用严重程度评分。
2. 估计表型与院内死亡的非因果性关联及其不确定性。
3. 评估早期贫血在各表型中的分布，并通过去除 Hb 的表型敏感性分析降低循环定义问题。
4. 评估 24h 窗口、完整病例、无 RBC、ICU LOS ≥48h、更严格动脉瘤证据、去除 INR/Hb、替代 GCS 表征和替代聚类算法下的结构稳健性。
5. 将 eICU 中的 frozen transport 视为已有结果知情的探索性外部验证；若要作确认性外部验证，应建立独立 protocol/manifest。

### 3.3 不属于本研究的目标

- 不估计 RBC 输血、贫血或任何 ICU 治疗的因果效应。
- 不声称已发现可直接用于临床决策的疾病亚型。
- 不把 phenotype × anemia 的差异解释为治疗效果异质性。
- 不把预测增量、SHAP-style 贡献或过程性治疗调整解释为致病机制。

## 4. 数据来源和 provenance

冻结代码引用以下 MIMIC-IV 3.1 BigQuery 模块：

- `physionet-data.mimiciv_3_1_hosp`
- `physionet-data.mimiciv_3_1_icu`
- `physionet-data.mimiciv_3_1_derived`

研究衍生表写入 `mimic-study-498508.non_traumatic_sah_study`。MIMIC-Note 和 MIMIC-ED 不属于主队列实现。数据版本、访问日期、关键 BigQuery job ID 和聚合 QC 已登记于 `reproducibility/run-manifest.yaml` 与 `reproducibility/freeze-validation.md`。社区 derived 表直接使用 PhysioNet 发布的 MIMIC-IV 3.1 BigQuery 版本；本仓库未检出独立的本地 MIMIC-Code checkout，因此不存在可登记的本地 commit。

主要可执行来源：

- 队列与特征：`10_create_non_traumatic_sah_cohort.sql`
- 表型与关联分析：`11_bigquery_notebook_non_traumatic_sah_analysis.py`
- 外部验证（探索性）：`14_create_eicu_external_validation_cohort.sql`、`scripts/15_run_eicu_external_validation.py`

## 5. 研究设计

回顾性、单数据库开发阶段的结构化 EHR 无监督表型研究，附带非因果性结局关联。主要表型发现使用 MIMIC-IV；表型发现过程中禁止使用院内死亡、ICU 死亡、LOS、贫血标签、RBC 输血或严重程度评分选择 K、拟合聚类或排序患者。

K=3 及当前特征集是在结果已被访问后锁定的分析选择，因此仅可称为“当前主分析”而非预设确认性主分析。K=4 为高分辨率探索性结果。

## 6. 研究人群

### 6.1 纳入标准

1. MIMIC-IV 3.1 `hosp.admissions` 中有 SAH 诊断：ICD-9 `430%` 或 ICD-10 `I60%`（移除小数点并大写后匹配）。
2. `anchor_age >= 18`。
3. 排除明确创伤性 SAH 后仍符合 non-traumatic SAH 定义。
4. 该住院存在 ICU stay。
5. 每次住院保留最早 ICU stay。
6. ICU LOS ≥24h。
7. 八项核心变量缺失数 ≤2。

### 6.2 当前实现中的主分析排除

主 discovery set 继续排除 ICU 入科后 0–24h `massive_transfusion_24h = 1`；其操作定义为 RBC 事件数 ≥5 或可换算单位总量 ≥5。该条件发生在 cohort entry 之后，因此冻结重跑必须同时执行 `eligible_include_massive_transfusion_sensitivity`，并在所有解释中限定主目标人群。

### 6.3 创伤性 SAH 排除

当前实现主要使用 ICD-10 `S06.6%` 标记创伤性 SAH。诊断标题文本规则、ICD-9 创伤相关编码覆盖和合并创伤诊断策略需纳入 codebook 审计，不能仅凭标题说明视为已验证。

### 6.4 重复结构

当前 SQL 按 `subject_id, hadm_id` 选择首次 ICU stay，但没有限定每个 `subject_id` 仅一次 SAH 住院。分析单元仍为 stay；同一患者可重复出现。冻结规则选择保留多住院，并要求所有 bootstrap、训练/验证划分和不确定性评估按 `subject_id` 分组。

## 7. 表型输入空间

主输入均来自 ICU 入科后半开窗口 `[icu_intime, icu_intime + 48h)`：

| 领域 | 主变量 | 聚合 | 临床范围（当前 SQL） | 主要来源 |
|---|---|---:|---:|---|
| 贫血 | `hb_min_48h_all` | 最低值 | >3 且 <25 g/dL | derived CBC |
| 神经 | `gcs_motor_min_48h` | 最低值 | 1–6 | derived GCS |
| 循环 | `map_min_48h` | 最低值 | 30–200 mmHg | derived vitalsign |
| 循环 | `shock_index_max_48h` | 最大值 | 0.1–5 | HR/SBP 最近邻匹配，±30 min |
| 氧合 | `spo2_min_48h` | 最低值 | 50–100% | derived vitalsign |
| 肾功能 | `creatinine_max_48h` | 最大值 | 0.1–20 mg/dL | derived chemistry |
| 凝血 | `inr_max_48h` | 最大值 | 0.5–20 | hosp labevents/d_labitems |
| 血小板 | `platelet_min_48h` | 最低值 | 10–1000 ×10³/µL | derived CBC |

结局、LOS、贫血二分类、输血、过程性治疗、严重程度评分、乳酸、肌钙蛋白、PaO2/FiO2、ePVS 和 sodium 不进入主聚类输入。

## 8. Timeline contract

| 时间字段 | 草案定义 | 来源/类型 | 状态与规则 |
|---|---|---|---|
| `eligibility_time` | 出院编码与完整住院资料可获得后回顾性判断 | diagnoses/admissions，`DATETIME`/discharge-coded | 本研究不是 ICU 入科时实时识别研究 |
| `cohort_entry_time` | 首次符合条件 ICU stay 的 `icu_intime` | icustays.intime，`DATETIME` | 无 delayed entry；但回顾性诊断在之后确认 |
| `index_time` | `icu_intime` | `DATETIME` | 仅为特征窗口锚点，不自动等于结局风险起点 |
| `feature_window_start` | `icu_intime`，含边界 | `DATETIME` | 所有主输入必须 `>= icu_intime` |
| `feature_window_end` | `icu_intime + 48h`，不含边界 | `DATETIME` | 当前 LOS 24–48h 者使用截短观察，可能有测量机会偏倚 |
| `prediction_landmark` | `not_applicable` | — | 本研究不是冻结的预测模型 |
| `target_ascertainment_window` | `not_applicable` | — | 非诊断预测研究 |
| `reference_standard_time` | `not_applicable` | — | 非诊断预测研究 |
| `treatment_assignment_time` | `not_applicable` | — | 不估计治疗效应 |
| `exposure_end` | `not_applicable` | — | phenotype 不是治疗暴露；构建完成时点为 48h |
| `followup_start` | `not_applicable`：同次住院描述性关联，不定义 landmark 风险起点 | — | 允许院内死亡与特征窗口重叠；不得声称 48h 后预测 |
| `censoring_time` | 二元院内死亡分析在 `dischtime` 结束 | `DATETIME` | 转院后结局不可见；活着出院不是长期生存随访 |
| `outcome_time` | `deathtime`（若住院死亡） | `DATETIME` | 需区分 48h 前死亡与 landmark 后死亡 |

同刻规则：事件时间等于 `feature_window_end` 时不计入特征窗口；若采用 48h landmark，必须在 landmark 时仍住院且存活。所有时间比较沿用 MIMIC BigQuery `DATETIME`，不进行真实时区推断。

## 9. 结局和外部判据

### 9.1 主要外部判据

院内全因死亡，来源为 `hospital_expire_flag`。它不进入聚类算法、PCA、插补、K 选择或表型严重度排序。

冻结选择为 **全住院描述性关联**：允许死亡发生在特征窗口内，表述为“同次住院中早期记录形成的表型与院内死亡共现”，不得称为 48h 后预后或预测。ICU LOS ≥48h 仍作为观察机会敏感性分析，不改变主目标。

### 9.2 次要结局

- ICU 死亡：仅描述；需明确死亡发生是否晚于表型窗口。
- ICU/住院 LOS：死亡截断明显，仅作描述或采用适当 competing-event 方法。
- 住院期 time-to-death：活着出院是竞争事件；当前把活着出院简单删失的 KM/Cox 仅为探索性，不能作为主要推断。
- SOFA、SAPS II、APS III、OASIS、LODS：只作外部严重程度判据，不进入聚类。

## 10. 暴露、描述变量和治疗变量

早期贫血定义为 0–48h 最低 Hb <10 g/dL；由于 Hb 同时属于聚类输入，贫血与 phenotype 的关系存在构造性依赖。主要描述可以报告贫血负担，但任何“贫血独立关联”必须以去 Hb 聚类作为关键敏感性分析。

RBC 输血、血管活性药、机械通气、EVD/ICP、CRRT、尼莫地平和液体平衡均发生在 0–48h 内，是疾病严重程度和临床决策共同决定的过程性变量。它们不属于基线混杂因素，不能在主要模型中被当作固定基线协变量进行因果调整。

## 11. 伦理、访问和隐私

本研究使用去标识化但受限访问的 PhysioNet 数据。每位接触数据的研究者必须独立满足 PhysioNet credentialing、培训和 DUA 要求，并遵守所在机构政策。不得提交凭据、患者级导出、逐行查询结果或可链接稀有组合。任何汇总表图公开前均需披露风险审查。

具体 IRB/伦理豁免编号、机构认定和数据访问批准信息为 `TBD`；不得用 MIMIC 去标识化状态替代机构要求。

## 12. 报告原则

- 遵循 STROBE cohort 与 RECORD。
- 报告完整 cohort flow、诊断 codebook、数据版本、窗口、缺失、聚类输入和算法参数。
- 表型只命名为 P1/P2/P3 或克制的生理描述，除非独立验证支持稳定临床标签。
- 主要报告效应量、95% CI、cluster size 和稳定性，不以单个 P 值决定表型真实性。
- 明确所有结果均为探索性、非因果性，并说明外部验证和前瞻性可用性验证仍需要独立证据。

## 13. 冻结门禁

- [x] 授权用户确认在合规环境使用 MIMIC-IV/eICU。
- [x] `run-manifest.yaml` 已登记 data release、访问日期和关键 job provenance。
- [x] non-traumatic SAH、创伤排除、动脉瘤证据和 RBC 定义已版本化并完成聚合 code audit；无人工病历金标准验证，作为限制保留。
- [x] 保留同一患者的多次住院，并将 bootstrap/交叉验证改为按 `subject_id` 分组。
- [x] 院内死亡冻结为全住院描述性关联，不定义 48h landmark 风险起点。
- [x] LOS 24–48h 保留在主描述性人群，LOS ≥48h 作为观察机会敏感性分析。
- [x] 主 discovery set 保留 post-entry 大量输血排除，并增加 include-all 敏感性分析标记与代码路径。
- [x] 样本数、独立患者数、重复 stay、各表型大小和主要事件已在聚合冻结证据中登记。
- [x] 所有已知结果知情设计选择已进入 `reproducibility/deviation-log.md`。
- [x] SAP 与冻结实现对齐，患者级 bootstrap 和完整预处理重拟合已执行。
- [x] 精确环境锁、运行证据、冻结时间和制品清单已登记；Git commit/tag 在本冻结事务末尾创建。
- [x] 小单元格已保守抑制；公开投稿前仍需机构/作者最终审批。

## 14. 版本历史

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-15 | DRAFT_BLOCKED | 根据现有公开代码和文档重建；明确结果已访问、治理限制、重复患者和时间契约阻塞项。 |
| 0.2.0 | 2026-07-16 | READY_FOR_AUTHORIZED_RUN | 冻结描述性目标、患者分组重采样和 include-all 大量输血敏感性分析；等待授权重跑与最终审查。 |
| 1.0.0 | 2026-07-16 | FROZEN_EXPLORATORY | 完成授权重跑、聚合 QC、结果对账、披露抑制和冻结清单；保持结果访问后的探索性定位。 |
