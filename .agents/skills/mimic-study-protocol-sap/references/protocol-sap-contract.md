# Protocol/SAP 冻结契约

## 目录

1. Protocol 最低字段
2. 时间契约
3. SAP 最低字段
4. 冻结记录
5. Deviation log
6. Go/no-go 检查

## 1. Protocol 最低字段

```yaml
study_id: "稳定且不含敏感信息的 ID"
title: ""
version: "0.1.0"
status: DRAFT
design_family: "descriptive | association | prediction | causal | phenotyping"
design_subtype: "not_applicable | diagnostic | prognostic | target_trial | iv | rd | did | its | other_with_gate_plan"
association_intent: "not_applicable | noncausal_adjusted | prognostic_factor"
modalities: ["structured"]
validation_role: "not_applicable | development | replication | external_validation | transportability"
confirmatory_status: "confirmatory | secondary | exploratory"
clinical_question: ""
clinical_decision_context: ""
data_sources_ref: "study-manifest.yaml#data.sources"
governance_decision_ref: ""
population:
  setting: ""
  eligibility: []
  exclusions: []
analysis_grain:
  unit: "subject | admission | stay | event | landmark | eligible_trial | clone | person_period"
  key_columns: []
  repeat_structure: "not_applicable"
estimand_or_target:
  population: ""
  strategies_or_predictors: ""
  comparator: ""
  outcome: ""
  horizon: ""
  intercurrent_events: ""
  summary_measure: ""
  contrast: ""
dag_ref: null # target_trial or confounding-adjustment design: "dag.md"
timeline_ref: "#timeline-contract"
primary_outcome: ""
secondary_outcomes: []
reporting_guidelines: []
preregistration:
  registry: null
  identifier: null
  registered_at: null
```

一份 study manifest 和冻结契约只对应一个主要科学问题。多主要问题研究必须拆分为独立 manifest/冻结契约，并在项目级索引中记录它们的关系，不能共享一个 `estimand_or_target` 或时间契约。`data_sources_ref` 必须逐项解析到 manifest 的 `data.sources`，以统一使用 `project`、`module`、`release`、`schema`、`access_date` 和 `linkage_provenance`，不得在 Protocol 中维护另一份来源版本事实。

`design_subtype` 对 prediction 和 causal 研究必填：prediction 使用 `diagnostic` 或 `prognostic`；causal 使用 `target_trial`、`iv`、`rd`、`did` 或 `its`。其他 design family 使用 `not_applicable`。无法归入现有 subtype 时仅可使用 `other_with_gate_plan`，并提供设计专属门禁计划。

`association` family 必须把 `association_intent` 设为 `noncausal_adjusted` 或 `prognostic_factor`，并预设 conditional/marginal target、固定 horizon 和 contrast；其他 family 使用 `not_applicable`。病因或治疗效应问题转入 causal family。

对 prediction 研究补充 intended use、prediction moment、target population、action triggered、prediction horizon 和 performance estimands。对 clustering/phenotyping 研究补充输入空间、相似度、稳定性目标和外部关联仅作验证而非聚类输入。

## 2. 时间契约

每个适用时间点都写定义、来源字段、粒度和允许关系：

| 字段 | 定义 | 必答问题 |
|---|---|---|
| `eligibility_time` | 判断资格的时点 | 所有资格信息在何时可用？ |
| `cohort_entry_time` | 进入研究队列的时点 | delayed entry 如何处理？ |
| `index_time` | 临床索引事件 | 是否只是标签，还是风险起点？ |
| `feature_window_start` | 表型或纵向特征输入窗口开始 | 输入从何时开始累计？ |
| `feature_window_end` | 输入窗口结束 | 下游结局比较是否晚于该时间？ |
| `prediction_landmark` | 发出预测且所有模型输入必须已可获得的时点 | 模型输入在此刻是否真实可用？ |
| `target_ascertainment_window` | 诊断目标被确认的观察窗口 | 是否与 predictor window 分离并避免 incorporation bias？ |
| `reference_standard_time` | 参考标准实施或可获得的时点 | 与预测发布的相对顺序是否明确，且适用于所有受试者？ |
| `treatment_assignment_time` | 分配或定义策略的时点 | grace period 是否产生 immortal time？ |
| `exposure_end` | 暴露分类窗口结束 | 早期死亡/出院如何分类？ |
| `followup_start` | 开始累计风险 | 与分配时间是否对齐？ |
| `censoring_time` | 停止观察 | 出院、转院、数据截止如何处理？ |
| `outcome_time` | 首次结局时点 | 竞争事件和复发事件如何处理？ |

时间字段在 manifest 模板中统一默认为 `not_applicable`；冻结前必须把适用字段替换为可执行定义，不适用字段保留该 canonical token。诊断预测研究必须明确 `target_ascertainment_window` 和 `reference_standard_time`，或逐项说明为何不适用。

每个数据元素还要记录：

```yaml
variable: ""
source_timestamp: ""
availability_time: ""
window: "[start, end)"
same_time_precedence: ""
timezone_or_type: "TIMESTAMP | DATETIME | DATE"
```

若 ICU 入科后 24 小时变量用于预测，通常应把 `prediction_landmark` 设为第 24 小时，并明确 landmark 前死亡/出院者不属于该时点的目标人群；不能仍声称在 ICU 入科时预测。

## 3. SAP 最低字段

### 样本量与事件数

记录总样本、独立患者、重复 stay、各暴露组、主要事件、竞争事件、随访量和缺失后的有效样本。根据研究类型说明：

- 效果估计：目标 CI 宽度、最小有意义差异、预期事件率、聚类/权重造成的设计效应；
- 生存分析：事件数、风险集、竞争事件、删失和最大参数自由度；
- 预测：目标参数数量、outcome prevalence、目标 shrinkage、calibration 精度和 optimism；
- 聚类/表型：维度、最小簇规模、重采样稳定性和可重复样本量。

如果数据集规模固定，进行 precision/power assessment，而不是把“使用全部 MIMIC 数据”当作样本量依据。不要把 10 events per variable 当作通用充分条件。

### 主要分析

```yaml
analysis_population: ""
descriptive_summary: ""
primary_model:
  formula: ""
  family_and_link: ""
  time_scale: null
  effect_measure: ""
  confidence_level: 0.95
  covariates_and_df: []
  nonlinear_terms: []
  interactions: []
  clustering_or_repeated_measures: ""
  assumptions_and_diagnostics: []
  prespecified_fallbacks: []
software:
  language: ""
  package_versions_lock: ""
  random_seed_policy: ""
```

### 缺失数据

逐变量/变量族记录结构性缺失、观测过程和时间可用性。预设 missingness 描述、主要方法和敏感性分析。多重插补需包含 outcome/暴露和合理辅助变量，并在 bootstrap/CV 训练折内拟合以防泄漏。说明插补次数选择和合并规则。不要默认使用 complete case、单次均值填补或 missing indicator。

### 多重性

```yaml
hypothesis_hierarchy:
  primary: []
  secondary: []
  exploratory: []
families: []
control_method: "alpha allocation | Holm | FDR | none with justification"
subgroups:
  prespecified: []
  interaction_test_required: true
```

### 最小敏感性矩阵

| 假设/风险 | 预设替代 | 稳健标准 |
|---|---|---|
| 队列定义 | 更严格/更宽定义 | 方向、量级和 CI 的解释规则 |
| 时间窗 | 合理临床窗口 | 风险集不引入 immortal time |
| 缺失 | alternative imputation/complete case | 结论差异的预设阈值 |
| 模型形式 | 非线性、稳健 SE、替代 link | 主要 estimand 保持一致 |
| 未测混杂 | negative control/E-value/bias analysis | 不把其当作消除混杂 |
| positivity | trimming/truncation/overlap population | 明确 estimand 是否改变 |
| competing risk | cause-specific/subdistribution/cumulative incidence | 与临床问题匹配 |

## 4. 冻结记录

`protocol-sap-lock.yaml` 至少包含：

```yaml
bundle_version: "1.0"
stage: protocol
study_id: ""
status: DRAFT | DRAFT_BLOCKED | FROZEN | AMENDED
protocol_version: ""
sap_version: ""
frozen_at: null
outcome_access_before_freeze: "none | blinded_qc | accessed"
artifacts:
  - role: protocol
    path: protocol.md
    version: ""
    sha256: ""
  - role: sap
    path: sap.md
    version: ""
    sha256: ""
  - role: dag
    path: dag.md
    version: ""
    sha256: "" # target_trial or confounding-adjustment designs only; omit otherwise
data_sources_ref: "study-manifest.yaml#data.sources"
code_commit: ""
codebook_version: ""
cohort_definition_version: ""
environment_lock: ""
approved_by: []
blockers: []
```

`study-manifest.yaml` 中 protocol stage 的 `artifact` 指向这个 bundle index，stage `sha256` 是该 index 自身的 hash。成员 hash 必须从最终文件计算；修改文件后旧 hash 失效，不能手改成看似有效。冻结记录只引用受控数据位置，不包含患者级内容。

## 5. Deviation log

采用永久追加记录：

```markdown
## DEV-0001 — YYYY-MM-DD
- Version affected:
- Requested by / approved by:
- Type: clarification | protocol amendment | SAP amendment | post hoc analysis
- Change:
- Reason and evidence:
- Outcome data seen: no | blinded only | yes
- Impact on estimand, bias, alpha, and interpretation:
- Disposition: retain confirmatory | relabel secondary | relabel exploratory | independent validation required
- Linked commit and artifacts:
```

不得删除已撤回的偏离；追加撤回状态及理由。

## 6. Go/no-go 检查

冻结前逐项回答：

- [ ] 治理决定覆盖所有输入、工具和输出。
- [ ] 数据项目、版本、访问时间和衍生构建可追溯。
- [ ] estimand/target 与设计专属分析计划一致；`target_trial` 的目标试验/DAG/调整集，或 IV/RD/DiD/ITS 的 assignment mechanism、专属假设与诊断一致。
- [ ] 所有适用时间点、窗口、早期事件和竞争事件已定义。
- [ ] 主要结局、分析人群和主要模型没有 `TBD`。
- [ ] 样本量/事件数论证与参数自由度一致。
- [ ] 缺失、多重性、验证、诊断和敏感性策略可执行。
- [ ] 输出表图与报告规范已映射。
- [ ] outcome access 状态真实记录。
- [ ] 文件 hash、代码 commit、环境锁和批准记录齐全。
- [ ] 空白 deviation log 已创建。

任一关键项未通过即 `DRAFT_BLOCKED`，不得生成虚假的冻结时间或批准者。
