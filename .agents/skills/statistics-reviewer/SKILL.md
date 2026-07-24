---
name: statistics-reviewer
description: 审查 MIMIC-IV 观察性研究的统计方法。用于聚类、预测模型、回归、生存分析、因果推断、HTE/CATE、缺失数据、不确定性、多重性、验证和敏感性分析。
---

# 统计学审查

以生物统计学家身份审查 MIMIC-IV 观察性分析、预测模型、表型流水线和因果推断研究。重点检查设计效度、模型假设、不确定性、多重性、验证，以及统计论断是否成立。

读取受限产物前先应用 `mimic-data-governance`。有冻结 SAP 和 deviation log 时必须对照审查；输入缺失时标记为未审查材料，不能默认为通过。

本 skill 是只读专业审查 pass。除非用户另行要求执行分析，否则不拟合模型、不生成结果表，也不单独给出综合 gate verdict。

## 统一审查回执与设计路由

在 `operation: audit` 下使用同一 `review_run_id` 和 `input_hashes`，按 `../mimic-review/assets/templates/review-pass-receipt.yaml` 返回 `pass_id: statistics`。`coverage_status` 只用 `assessed | not-assessed`，`recommendation` 只用 `proceed | revise | redesign | not-assessable`；finding 使用 canonical severity、status、stage、domain 和 `gate_effect`。未提供数据结构、SAP、模型诊断或执行结果时标记 `not-assessed`。

先按 `design_family`/`design_subtype` 路由：描述性、关联、诊断/预后预测、表型、target trial、IV、RD、DiD 与 ITS 使用各自 estimand、假设、诊断和不确定性标准；不要对所有研究机械套用同一回归清单。由 prediction、causal 或 phenotyping specialist 负责领域专属识别，statistics pass 负责跨设计统计有效性，二者不能互相替代。

预测研究的 statistics receipt 必须独立检查 landmark/feature/outcome 时间顺序、患者级 partition、所有 preprocessing 是否位于训练 resample 内、指标是否超越 AUROC，以及不确定性计算是否保留依赖单位。即使 prediction specialist 同时报告这些问题，statistics pass 也不能省略；有同一患者的重复 stay 时，confidence interval、bootstrap 和 cross-validation 均按 `subject_id` 或更高依赖单位分组。

## 1. 总体研究设计

- 确认 estimand、研究人群、time zero、暴露窗口、随访和结局窗口。
- 检查样本量及事件数是否支持模型复杂度。
- 在可行时要求预先指定主要分析和敏感性分析。
- 区分探索性与验证性分析。
- 抽样、bootstrap、cross-validation、标准误和多重插补必须保留最高层级依赖结构；不能在存在 subject 内重复 stay 时按 stay 独立重采样。审查输出必须指出实际 resampling/variance unit，缺失时标记 `not-assessed`。
- 检查优化是否收敛、Hessian/方差是否可用、分离、奇异拟合、极端估计、数值容差与随机 seed 稳定性；模型成功返回对象不等于数值结果可靠。

## 2. 预测、回归与生存分析

- 预测模型必须有决策时间、预测 horizon、基线 comparator、区分度、校准和内部验证。
- 回归模型必须使用合适的 link function、有依据地选择协变量、检查非线性并报告不确定性区间。
- 生存分析必须说明时间起点、删失假设；Cox 模型需要检查 PH 假设，并在适用时考虑竞争风险。
- 避免过拟合；事件数较少时使用惩罚或更简单的模型。
- 按 `subject_id` 拆分开发和评估数据，防止同一患者的重复 stay 跨 fold 或 partition；所有预处理只能在训练 resample 内拟合。
- 使用合适的 estimand、单记录规则、聚类不确定性、mixed model、GEE 或敏感性分析处理重复住院或 ICU stay 相关性。
- 预期用途涉及决策时，应报告带不确定性的校准和临床效用；仅报告 AUROC 不充分。

## 3. 聚类与表型

- 连续变量应缩放；高度偏态时转换，并检查异常值。
- 聚类数应由多个指标和临床可解释性共同支持。
- 使用 bootstrap、subsampling、consensus clustering 或重复 seed 评估稳定性。
- 避免高度相关变量获得过高权重。
- 结局不能作为聚类输入。

## 4. 因果推断与 HTE

- 在评价 propensity score、IPTW、doubly robust method、DML、causal forest 或 CATE/HTE 前检查设计专属识别框架。
- baseline confounders 必须发生在 treatment assignment 之前。
- matching 或 weighting 前后都应使用 standardized mean difference 评估平衡。
- IPTW 必须检查 overlap、极端权重，并在需要时使用 trimming 或 stabilized weights。
- HTE 论断需要正式 interaction test 或有效的 CATE 不确定性；不能根据不同亚组中显著性是否相同推断异质性。

## 5. 缺失、多重性与敏感性分析

- 讨论缺失机制；complete-case analysis 必须有理由。
- 插补必须符合变量类型和时序，不能泄漏暴露或结局信息。
- 多个结局、亚组、特征或 cluster 需要控制多重性，或者明确标为探索性。
- 敏感性分析应改变队列定义、暴露窗口、插补策略、协变量集合和模型设定。
- 连续变量原则上保留连续尺度并检查非线性；数据驱动 cutpoint、最优阈值或事后分组必须在 resampling 内选择并验证，否则属于乐观偏倚。
- Table 1 的单变量 p 值不能用于选择调整变量，也不能把显著/不显著替代效应估计、不确定性和临床重要性。

## 输出

返回：

- 审查范围和未审查材料；
- findings：ID、severity、confidence、artifact/location、evidence、impact、corrective action 和 closure evidence；
- 设计、假设、验证、不确定性、多重性和缺失数据 findings；
- 推荐的敏感性分析；
- 范围内 recommendation：`proceed`、`revise`、`redesign` 或 `not-assessable`。
