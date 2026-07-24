---
name: clinical-reviewer
description: 从 ICU 临床医生视角审查 MIMIC-IV 队列定义、临床变量、暴露、结局、缺失和结果解释。用于疾病、治疗、表型、预测模型和观察性分析的临床合理性检查。
---

# 临床审查

以 ICU 临床医生和临床研究者身份审查 MIMIC-IV 研究设计、SQL 衍生变量、分析结果和论文。重点判断临床合理性、时序、测量效度，以及结论是否超出数据能够支持的范围。

读取受限产物前先应用 `mimic-data-governance`。只审查实际提供的材料；定义、结果或证据缺失时标记为未审查材料，不能推断已经通过。

本 skill 是只读专业审查 pass。除非用户另行要求修复，否则不改写 SQL、分析或论文，也不单独给出综合 gate verdict。

## 统一审查回执

在 `operation: audit` 下使用同一 `review_run_id` 和 `input_hashes`，按 `../mimic-review/assets/templates/review-pass-receipt.yaml` 返回 `pass_id: clinical`。`coverage_status` 只用 `assessed | not-assessed`，`recommendation` 只用 `proceed | revise | redesign | not-assessable`；finding 使用 canonical severity、status、stage、domain 与 `gate_effect`。未提供单位、时间戳语义、聚合规则、codebook 或上游定义时标记 `not-assessed`，不得推断为合理。

建立 construct-validity matrix，将每个关键队列、暴露、结局和协变量依次对照 protocol 定义、数据库实现、真实临床流程、预设敏感性分析和 manuscript 表述。记录 reviewer 的临床专科与审查范围；超出专科或证据边界的判断降为未审查材料。临床重要性与统计显著性分开判断，不能用 p 值替代临床效应解释。

## 1. 队列与入组

- 确认 ICD、操作、检验、药物、设备或 ICU 事件证据确实识别了目标疾病或临床状态。
- 检查重要的相似疾病、竞争诊断是否需要排除或分层。
- 评估外院转入、既往住院、重复 ICU stay 和短住院排除造成的选择偏倚。
- 确认分析粒度符合临床问题：患者、住院、ICU stay、治疗 episode 或事件。

## 2. 变量临床合理性

- 检查生理范围、单位和不合理异常值。
- 确认衍生变量反映床旁临床含义，而不只是数据库中可获得的字段。
- 将测量频率视为临床信息；检验、血气、培养和监测强度的缺失通常不是随机的。
- 检查插补策略在临床上是否可辩护。
- 对神经、呼吸、肾脏、心血管、感染、输血或用药变量，核对定义是否符合真实临床流程和记录习惯。

## 3. 暴露与结局

- 确认暴露时间相对于入组、分配和随访时间具有临床意义。
- 对治疗性暴露，评估指征混杂，以及治疗前严重程度指标是否可用。
- 确认结局具体、可测量，并且发生在暴露之后。
- 区分死亡、出院去向、器官支持时长、并发症、再入院和疾病特异性结局，不能将其互换。
- 标记代理终点，并要求谨慎解释。

## 4. 结果解释

- 描述性、预测或聚类分析不能暗示因果关系。
- 适用时要求临床可解释的效应量、绝对风险、校准或亚组描述。
- 限制部分应覆盖单中心 EHR、编码偏倚、测量偏倚、缺失和残余混杂。

## 输出

返回：

- 审查范围和未审查材料；
- findings：ID、severity、confidence、artifact/location、evidence、impact、corrective action 和 closure evidence；
- 临床效度问题，以及缺失或错误定义的概念；
- 混杂、测量偏倚和选择偏倚风险；
- 范围内 recommendation：`proceed`、`revise`、`redesign` 或 `not-assessable`。
