---
name: mimic-external-validation
description: Plan and implement external validation of MIMIC-derived cohorts, phenotypes, and models in eICU or other ICU datasets. Use for variable harmonization, cohort-definition transport, feature availability matrices, unit conversion, model freezing, calibration, discrimination, phenotype assignment, and transportability limitations.
---

# MIMIC External Validation

用这个 skill 将 MIMIC-IV 中开发的 cohort、phenotype 或 model 迁移到 eICU、HiRID、AmsterdamUMCdb 或其他 ICU 数据集做外部验证。核心是先做 definition transport 和 variable harmonization，再评估性能。

先应用 `mimic-data-governance` 及各外部数据源的数据治理协议；MIMIC 的 DUA 不自动授权使用或共享外部数据库。输出必须包含可执行的 mapping artifact 和冻结规则，不能只给建议清单。

## 先确认验证对象

- 验证 cohort definition？
- 验证 clustering phenotype 可复现？
- 验证 prediction model？
- 验证 treatment effect 或 subgroup signal？
- 目标总体和 transport estimand 是什么？是否需要 selection/transport weighting？

不同对象需要不同证据，不要混用。

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
