---
name: mimic-causal-analysis-guardrails
description: Apply causal-inference guardrails to MIMIC-IV observational studies. Use for target trial emulation, treatment effects, propensity scores, IPTW, DML, CATE/HTE, instrumental variables (IV), regression discontinuity (RD), difference-in-differences (DiD), interrupted time series (ITS), immortal time bias, positivity, and cautious causal interpretation.
---

# MIMIC Causal Analysis Guardrails

用这个 skill 审查或设计 MIMIC-IV 中的治疗效应、HTE/CATE、因果森林、DML、IPTW 等观察性因果分析。目标是先让时间顺序和 estimand 成立，再谈模型复杂度。

读取患者级数据前先应用 `mimic-data-governance`。使用 `mimic-study-protocol-sap` 冻结因果 subtype、estimand、识别契约、主要分析和偏离记录。

## 选择操作

- `operation: build`：设计或实现因果分析。
- `operation: audit`：只读审查冻结设计、实现、诊断和结果；不得重写 estimand、执行分析、调权重或为当前结果补造识别假设。

audit 由 `mimic-review` 调用时，使用同一 `review_run_id` 与 `input_hashes`，按 `../mimic-review/assets/templates/review-pass-receipt.yaml` 返回 `pass_id: causal`、`coverage_status`、`recommendation`、canonical findings 和 `gate_effect`；缺少识别证据或 subtype-specific diagnostics 时标记 `not-assessed`。每个 finding 必须说明可修复问题或 stop/redesign condition。time zero、未来治疗分组、无有效风险集或 estimand 与实现不一致通常使用 `gate_effect: requires_redesign`，而不是建议表面修稿。

## 先选择因果设计 subtype

- `target_trial`：显式比较治疗策略，冻结目标试验、time zero、策略、estimand 和混杂控制。
- `iv`：冻结 instrument、relevance、exclusion restriction、independence 和 monotonicity 等适用假设与诊断。
- `rd`：冻结 assignment variable、cutoff、continuity、manipulation 检查、bandwidth 和 estimand。
- `did`：冻结干预时点、对照组、parallel trends、anticipation、动态效应和聚类推断。
- `its`：冻结中断点、趋势模型、并发干预、季节性、自相关和稳健性分析。

下列目标试验要素只对 `target_trial` subtype 强制；其他 subtype 使用各自的识别契约。

## 写清 target trial

- Eligibility：谁在 `eligibility_time` 时符合入组？
- Treatment strategies：治疗 vs 对照如何定义？
- Assignment time：治疗分配发生在何时？
- Grace period：治疗策略是否允许延迟开始，如何避免用未来治疗定义 baseline 组？
- Follow-up：从何时开始，到何时结束？
- Outcome：主要结局和时间窗是什么？
- Causal contrast：ATE、ATT、CATE、risk difference、odds ratio 还是 survival contrast？

如果这些不能写清，不要直接上 causal forest 或 DML。

## Target-trial 时间与混杂门禁

- baseline confounders 必须在 `treatment_assignment_time` 前或当时已可获得，且不受治疗影响。
- 分别定义 `eligibility_time`、`treatment_assignment_time`、`exposure_end` 和 `followup_start`，不要用一个 `T0` 代替。
- grace period 不得自动推迟 `followup_start`；通常从共同 time zero 开始随访，并按设计采用 cloning/censoring/weighting、序贯试验或其他有效策略。若条件于存活至 grace period 结束，必须声明目标总体和 estimand 已改变。
- outcome 必须从统一 follow-up start 后观察。
- 避免 immortal time bias：不要把“未来才会发生的治疗”当作 baseline group。
- 不要把 post-treatment mediators/colliders 放进 baseline adjustment。

## Target-trial 混杂与 positivity

- 列出最小必要 confounder set，说明临床理由。
- 检查 treatment group 与 control group 的 overlap。
- 报告极端 propensity scores 或权重截断。
- 如果某些亚组几乎不可能接受治疗，HTE 解释必须收缩。

## 方法选择

- Propensity score matching/weighting：适合清晰二分类治疗，需 balance diagnostics。
- Doubly robust / AIPW / DML：适合较多 confounders，但仍依赖设计正确。
- Causal forest / HTE：用于探索异质性，必须报告不确定性和稳定性。
- Sensitivity analysis：用于未测混杂和定义变动。

以上 propensity-score、balance 和 positivity 门禁适用于 target-trial/混杂调整分析，不得机械套用于其他 subtype。其他 subtype 至少执行：

- **IV**：报告 first-stage/relevance、弱工具诊断、方向/单调性、排除限制与独立性依据，并明确 LATE 等实际 estimand。
- **RD**：报告 cutoff、带宽选择、密度/操纵检验、协变量连续性、函数形式与 donut/placebo sensitivity。
- **DiD**：报告处理时点与对照、事件研究、处理前趋势、anticipation、错位实施处理和适当聚类标准误。
- **ITS**：报告中断点、基线趋势、水平/斜率变化、季节性、自相关、并发干预和伪中断点分析。

对无法直接检验的关键假设，明确其临床/制度依据、可证伪含义和 quantitative bias analysis 或 negative-control 证据（适用时）；未检验不等于已满足。弱 IV 应采用与弱工具相容的区间或稳健推断。错位实施的 DiD 不得依赖已知对异质处理效应有偏的单一 two-way fixed-effects 汇总，需审查 cohort/time-specific estimand。TARGET 只在其正式范围内用于 target-trial emulation，不能给 IV、RD、DiD 或 ITS 套用。

## 禁止事项

- 不要把预测模型性能当作因果识别证据。
- 不要因为模型支持 CATE 就声称发现治疗效应修饰。
- 不要用 post-treatment lab/vital 调整 treatment effect。
- 不要忽略 missingness 与 measurement intensity 的信息性。

## 报告要求

- 说明 estimand。
- target-trial/混杂调整分析报告 cohort flow、treatment counts、baseline balance 和 positivity/overlap；IV/RD/DiD/ITS 改为报告其专属样本结构、assignment diagnostics 和识别检查。
- 报告 effect estimate uncertainty。
- 明确 exploratory 与 confirmatory 区别。
- 在 limitations 中说明 residual confounding、measurement error 和 single-center 数据限制。
- Target trial emulation 在 TARGET 2025 正式范围内将其作为 standalone 主报告清单，并逐项说明理想试验与观察性模拟之间的偏离。
- IV、RD、DiD、ITS 不因属于 causal family 自动使用 TARGET；应采用设计专属报告规范并核验目标期刊要求。
