---
name: mimic-study-protocol-sap
description: Draft, audit, version, and freeze a reproducible MIMIC study protocol and statistical analysis plan before confirmatory analysis. Use when defining an estimand, DAG, cohort and analysis populations, explicit clinical timeline, sample-size or event-count rationale, missing-data and multiplicity strategies, primary models, validation, sensitivity analyses, deviation logging, preregistration, or a protocol/SAP go-no-go gate.
---

# MIMIC Study Protocol and SAP

在查看主要结局分布或调整确认性分析之前，生成可冻结、可审计的 protocol/SAP。不要把未决定事项伪装成已定方案；保留 `TBD` 并维持 `DRAFT`，直到门禁全部通过。

## 先运行前置门禁

1. 对任何真实 MIMIC 文件先调用 `mimic-data-governance`。没有允许决定时，只使用公开 schema、文献和合成数据。
2. 记录一个主要研究问题、临床决策场景、`design_family`、适用的 `design_subtype`、关联研究的 `association_intent`、逐来源项目的精确版本/schema/linkage provenance、结构化分析粒度和报告规范。
3. 区分 `confirmatory`、`secondary` 与 `exploratory`。已经查看结局后提出的假设不得追溯标为预设。
4. 复用已有 cohort、codebook 和时间定义；冲突时列为 blocker，不静默选择一个版本。

## 固定研究问题与 estimand

使用一句话说明目标人群、暴露/策略、对照、结局和时间范围。所有因果研究都必须固定：

- population 与 eligibility；
- outcome 定义与 horizon；
- population-level summary 与 contrast，例如 risk difference、risk ratio、hazard contrast、ATE 或 ATT。

`target_trial` subtype 还必须固定 treatment/exposure strategies、允许的 grace period、assignment/time zero、intercurrent events 和 censoring。`iv`、`rd`、`did`、`its` 则冻结各自的 assignment mechanism、设计专属识别假设、诊断与敏感性分析，不能用目标试验字段代替。

对描述、预测、表型或外部验证研究，改写为相应目标参数或 prediction target，并明确目标使用时点、预测 horizon 与评价对象。不要把关联 estimand 描述为因果效应。

## 按因果 subtype 冻结识别契约

`target_trial` 或依赖混杂调整的因果研究应冻结 DAG 与调整集。IV、RD、DiD、ITS 等设计不得被强制伪装成目标试验；它们应冻结各自的 assignment mechanism、排除限制/连续性/平行趋势等适用假设、诊断和失效条件。描述、预测、表型及不作因果解释的普通关联研究不得因为缺少 DAG 而阻塞。

- 标记 exposure/treatment、outcome、baseline causes、mediators、colliders、selection nodes 和未测变量。
- 为每条关键边给出临床或文献依据；将不确定边保留为备选 DAG，并映射到敏感性分析。
- 从 DAG 推导最小充分调整集，再和可测变量、时间顺序及测量质量核对。
- 不把治疗后变量、mediator 或 collider 填入 baseline adjustment。预测模型若使用治疗后信息，必须相对 prediction landmark 重新标时。
- 把 DAG 源文件及版本纳入冻结包；纯文字变量列表不能代替因果结构。

## 使用明确时间契约

不要让单个 `T0` 同时承担入组、暴露分配、预测和随访开始。逐项定义适用的时间点：

```text
eligibility_time
cohort_entry_time
index_time
feature_window_start
feature_window_end
prediction_landmark
target_ascertainment_window
reference_standard_time
treatment_assignment_time
exposure_end
followup_start
censoring_time
outcome_time
```

为每个协变量、暴露与结局记录 source timestamp、可用时间、半开窗口 `[start, end)`、同刻事件优先级和 BigQuery 时间类型。明确早期死亡、出院、转院、重复 ICU stay、landmark 前退出、竞争事件和 delayed entry 的风险集处理。时间逻辑不完整时禁止冻结。

## 写作 SAP

依次固定以下内容，完整字段见 `references/protocol-sap-contract.md`：

1. **分析人群与粒度**：记录 `unit`、`key_columns` 和 `repeat_structure`；unit 可为 subject、admission、stay、event、landmark、eligible_trial、clone 或 person_period，并定义主分析集和敏感性分析集。
2. **结局与变量**：主要结局只指定一个或明确共同主要策略；锁定 codebook 版本、单位、派生规则和盲态 QC。
3. **样本量与信息量**：报告可用人数、独立患者数、各组人数、主要事件数、竞争事件和有效聚类数；用目标精度、可检测效应或适合模型的样本量方法论证，不机械套用固定 EPV。
4. **主要模型**：给出公式、时间尺度、效应度量、link、协变量自由度、非线性、交互、重复测量/聚类、假设诊断和失败时的预设替代。
5. **缺失数据**：区分结构性缺失、未测量与测量失败；描述缺失模式、主要处理、插补模型、辅助变量、插补次数及在 resampling 内防泄漏的实现。
6. **多重性**：建立 primary/secondary/exploratory 层级、检验族、alpha 分配或 FDR 方法；未经校正的探索结果只报告效应与不确定性并明确标注。
7. **验证与不确定性**：按设计固定 confidence interval、bootstrap/cross-validation、校准、稳定性、模型假设、稳健标准误或其他适用的不确定性方法；涉及数据拆分时按患者分组。
8. **敏感性分析**：为每项识别假设、时间窗、队列定义、缺失策略、未测混杂或模型选择指定可证伪的替代分析与解释阈值。
9. **输出**：按设计预先列出 flow diagram、描述表、主要估计或模型/表型结果、诊断图、缺失表、敏感性矩阵和 supplementary material；不把 Table 1、ROC 或效应表强制用于不适用的设计。

## 冻结门禁

只有以下条件全部成立才能将状态改为 `FROZEN`：

- 数据治理决定允许计划中的处理环境；
- protocol、estimand/target、时间契约和适用的 outcome/target 没有 `TBD`；`target_trial` 的目标试验/DAG/识别假设或其他因果 subtype 的专属识别契约也没有 `TBD`；
- 数据源、版本、队列、codebook、analysis unit 和分析人群可追溯；
- 样本量/事件数依据、主要模型、缺失、多重性、验证和敏感性策略完整；
- 产物具有版本、内容 hash、冻结时间、责任人/批准方式和代码 commit；
- 任何结局知情的设计变化都已披露；
- deviation log 已创建，即使当前为空。

门禁失败时输出 `DRAFT_BLOCKED` 和阻塞项。可在合成或盲态数据上编写与测试 pipeline，但不得把结局驱动调参结果当作预设确认性分析。

## 输出契约

输出或更新以下冻结包：

```text
protocol.md
sap.md
dag.md                 # target_trial/混杂调整设计适用；Mermaid/DAGitty 源码与变量字典
protocol-sap-lock.yaml # 状态、版本、hash、数据/代码版本和批准记录
deviations.md          # 永久追加式变更记录
```

如项目已有 `study-manifest.yaml`，将上述文件逐项登记到 protocol stage 的 bundle index，并只把该 index 的路径和 hash 写入 manifest，不复制另一套事实。模板和验收字段见 `references/protocol-sap-contract.md`。

## 变更与偏离

- 冻结后不得覆盖旧版本。创建新版本并在 `deviations.md` 记录时间、发起人、触发证据、是否查看结局、影响分析、批准和处置。
- 将实现性澄清、protocol amendment、SAP amendment 与 post hoc analysis 分开标记。
- 结局知情的改变默认降为 exploratory；只有在独立数据或明确的再验证计划下才能恢复确认性定位。
- 论文逐项对照冻结版本，披露所有实质偏离和最终分析时间戳。
