---
name: mimic-external-validation
description: Plan, implement, and audit external validation of MIMIC-derived cohorts, phenotypes, and models in eICU or other ICU datasets. Use for variable harmonization, cohort-definition transport, feature availability matrices, unit conversion, model freezing, calibration, discrimination, phenotype assignment, and transportability limitations.
---

# MIMIC External Validation

用这个 skill 将 MIMIC-IV 中开发的 cohort、phenotype 或 model 迁移到 eICU、HiRID、AmsterdamUMCdb 或其他 ICU 数据集做外部验证。核心是先做 definition transport 和 variable harmonization，再评估性能。

先应用 `mimic-data-governance` 及各外部数据源的数据治理协议；MIMIC 的 DUA 不自动授权使用或共享外部数据库。输出必须包含可执行的 mapping artifact 和冻结规则，不能只给建议清单。

## 选择操作

- `operation: build`：规划或实施验证与 transport。
- `operation: audit`：只读审查现有 frozen object、mapping、plan、results 和 claims；不得重新训练、重新聚类、映射变量、校准或更新模型。

audit 由 `mimic-review` 调用时，使用同一 `review_run_id` 和 `input_hashes`，按 `../mimic-review/assets/templates/review-pass-receipt.yaml` 返回 `pass_id: external-validation`、`coverage_status`、`recommendation`、canonical findings 和 `gate_effect`；缺少 frozen rule、独立数据关系、样本/事件数、精度或 mapping 证据时标记 `not-assessed`。

## 先确认验证对象

- 验证 cohort definition？
- 验证 clustering phenotype 可复现？
- 验证 prediction model？
- 验证 treatment effect 或 subgroup signal？
- 目标总体和 transport estimand 是什么？是否需要 selection/transport weighting？

不同对象需要不同证据，不要混用。

先给验证类型定名：temporal、geographic、different-setting、internal-external、replication、transport 或 update。再区分 `pure evaluation`、预设 recalibration-in-the-large、其他 recalibration 与 model updating；任何更新后的对象都不能继续冒充原模型的纯外部验证。表型在外部库 outcome-informed re-clustering 属于重新发现，不是冻结 assignment rule 的 external validation。

## 变量映射

- 建立 feature availability matrix：MIMIC feature、外部库变量、单位、时间戳、缺失率、是否可替代。
- 明确每个变量是 exact match、proxy、unavailable 还是 not comparable。
- 单位必须转换并记录。
- 时间窗必须尽量对齐，例如 ICU 入科后 `0-48h`。
- 外部库没有的变量不要用 outcome-adjacent proxy 偷换。

## Cohort transport

- 诊断编码体系、ICU stay 定义、入院时间和死亡时间可能不同。
- inclusion/exclusion criteria 应逐条映射。
- 如果无法完整复现，记录 deviation，并做敏感性分析。
- 输出外部验证 cohort flow。

## 模型/表型验证

- prediction model：冻结 feature set、preprocessing、coefficients 或 trained pipeline；外部 evaluation 的 subject/episode 不得参与训练、调参、模型选择或校准，并说明属于 temporal、geographic、different-setting 或其他验证及其数据来源关系。
- prediction metrics：分开报告 discrimination、calibration、Brier/log score 等总体概率评分和适用的 clinical utility；time-to-event 模型使用 censoring/competing-risk-aware 的 horizon-specific 指标。
- clustering phenotype：优先用 MIMIC 训练好的 scaler/centroids 或 assignment rule 分配外部患者；不要在外部数据重新聚类后声称同一 phenotype。
- association validation：预先定义方向和模型，避免事后解释。
- prediction model：预先定义仅评估、截距更新、再校准或完整更新的决策规则；不得看结果后静默选择更新方式。
- treatment effect：定义目标总体、可运输性假设和选择机制；需要时报告 selection/transport weights 与诊断。

## Transportability 限制

- ICU 类型、数据采集频率、单位、治疗实践和 missingness 都可能变化。
- 外部验证失败不一定表示原模型无效，也可能是变量映射或 population shift。
- 报告 external cohort 与 MIMIC derivation cohort 的差异。
- 报告目标样本数、事件数/cluster support、关键指标或估计的区间精度；不能只凭一个点估计宣布成功或失败。
- 因果 effect transport/replication 必须依赖 `causal` pass 的 estimand、识别与可运输性假设审查；本 skill 不单独证明因果识别。

## 完成前检查

- 变量映射表存在。
- 单位转换已记录。
- 模型或 phenotype assignment 是否冻结已说明。
- calibration 和 discrimination 分开报告。
- evaluation cohort 与开发、调参、选择和校准数据相互独立，验证类型与来源关系已声明。
- 生存/竞争风险模型使用相应的删失与竞争事件感知指标。
- 不可映射变量没有被静默删除而不说明。

## 必需产物

- `cohort-mapping`：逐条 eligibility 与偏离。
- `feature-availability`：源变量、目标变量、单位、时间、代理级别、缺失率。
- `frozen-transform`：预处理、模型/centroid/assignment rule 的版本和 hash。
- `validation-plan`：验证类型、数据独立性、主要指标、置信区间、更新规则和亚组。
- `validation-results`：样本流、population shift、性能、校准、clinical utility 和 not-assessed 项。
