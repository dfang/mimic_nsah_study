---
name: mimic-research-topic-scout
description: Use when initiating or refining MIMIC-IV research topic ideation, screening novelty and clinical relevance, triaging topic-stage data feasibility before protocol design, estimating journal positioning, or rejecting duplicative, low-value, and unanswerable study questions.
---

# MIMIC Research Topic Scout

## Overview

把宽泛疾病方向、临床困惑或投稿目标转化为值得验证的 MIMIC-IV 研究问题。依次回答三个问题：

1. **值不值得做？** (创新性和临床价值是否都足够)
2. **能不能做？**
3. **做出来能发表到哪里？**

执行顺序：Gate 1 值不值得做 → Gate 2 能不能做 → Gate 3 做出来能发表到哪里 → 最终动作。

默认评估结构化 MIMIC-IV/BigQuery 研究。读取任何受限样本或研究工作区前先应用 `mimic-data-governance`。仅使用公开 schema、文献和汇总元数据时，不读取或展示患者行。

## Boundary

只负责选题与分流：

- 已确定选题并需完整 protocol/SAP：使用 `mimic-study-protocol-sap`。
- 需构建队列或编写 SQL：使用 `mimic-cohort-builder`；审计 SQL 使用 `mimic-bigquery-qc`。
- 需训练预测模型、实施表型分析或因果分析：分别使用 `mimic-prediction-modeling`、`mimic-phenotyping-pipeline` 或 `mimic-causal-analysis-guardrails`。

不要在本阶段写完整时间契约、模型验证方案、因果识别细则、统计代码或最终图表计划。

## Quick reference

| Layer | Field | Allowed values / required fields |
|---|---|---|
| Gate 1 | `innovation_status` | `duplicative`, `incremental`, `substantive`, `evidence_pending` |
| Gate 1 | `contribution_path` | `fill_gap`, `deepen_evidence`, `independent_validation`, `duplicative`, `unclear` |
| Gate 1 | `clinical_value_status` | `decision_relevant`, `knowledge_relevant`, `weak`, `unclear` |
| Gate 1 | `worth_status` | `WORTH_ADVANCING`, `EVIDENCE_PENDING`, `REFRAME`, `DROP` |
| Gate 2 | `feasibility_status` | `FEASIBLE`, `AUDIT_REQUIRED`, `REDESIGN`, `NOT_FEASIBLE` |
| Gate 3 | publication ceiling | `current_ceiling`, `ceiling_blockers`, `upgrade_path`, `confidence` |
| Decision | `action` | `advance_to_audit`, `reframe`, `park`, `drop` |

## 先限定选题空间

必要时确认：

- 疾病、人群、临床场景或核心知识缺口；
- 预期贡献类型：描述、关联、预测、表型或治疗效果；
- 可使用的 MIMIC 模块、外部数据、团队能力和执行环境；
- 目标读者、期刊家族、文章类型或期望层级。

缺失信息允许标为未知并继续初筛，不要用未经核验的假设填空。

## 第一层：值不值得做 —— 创新性与临床价值

把创新性和临床价值作为两个独立门槛，先判断是否值得做，再讨论数据库和方法。疾病重要、结局严重或技术新颖，都不能单独证明题目值得做。

1. 调用 `mimic-literature-evidence` 做广泛 novelty 检索，不要停在少量命中或搜索摘要。至少检索一个生物医学数据库，并在可访问时加入一个互补来源；同时覆盖 MIMIC 特异研究、广义临床问题、系统综述/指南、注册研究或预印本及前后向引文追踪。记录每个来源的检索日期、完整 query、原始结果数、筛选范围、最近似研究、访问限制和检索饱和度。不能完成上述覆盖时明确降级为初筛。
2. **创新性门槛**：用一句话说明真实证据缺口及与最近似研究的实质差异。不要因某个精确关键词无结果就声称空白；比较人群、临床场景、estimand/目标、暴露或策略、结局、时间范围、数据源和验证设置后，再判断贡献路径。
3. **临床价值门槛**：说明谁会使用或从结果中获益、处于什么临床/知识场景、可能改变什么决策或认识、患者重要结局是什么，以及阴性结果是否仍有信息价值。
4. 分别输出 `innovation_status`、`contribution_path` 与 `clinical_value_status`，再给出综合 `worth_status`。不要用临床价值掩盖重复性，也不要用技术新颖掩盖无临床/科学后果。

`WORTH_ADVANCING` 要求创新贡献与临床/科学后果均已核验；文献未充分核验时使用 `EVIDENCE_PENDING`；一项门槛不足但可挽救时使用 `REFRAME`；重复、平庸或没有可信后果时使用 `DROP`。分别给出状态证据与置信度。

为每个候选题注明知识贡献路径：

- `fill_gap`：广泛检索后没有研究直接回答该临床问题，且空白不是由无意义的算法、亚组或措辞差异制造；明确将填补什么空白。
- `deepen_evidence`：已有研究，但存在会改变结论或临床解释的关键局限；明确要深入哪一项局限以及新增证据为何重要。
- `independent_validation`：核心问题已有答案，但缺少预设的跨时间、跨数据库或跨机构验证；明确验证对象与失败仍有何价值。
- `duplicative`：最近似研究已充分回答，新增设计不能解决重要不确定性。
- `unclear`：检索覆盖、全文获取或证据核验不足，暂不能判断。

只有广泛检索达到声明的覆盖范围，才能使用 `fill_gap`。`deepen_evidence` 必须指出现有研究的具体限制，不能只说“样本不同”或“方法可以更复杂”。预设的独立复现若解决重要不确定性，可以属于有价值的增量贡献。

只有创新性与临床价值两个门槛都通过，才可给 `WORTH_ADVANCING`。未完成最近似文献核验时，不得确认实质创新，也不得给出高发表上限。第一层为 `DROP` 时停止细化，只可提供一个明确不同的重构方向。

## 第二层：能不能做

只检查选题级可行性，不提前设计完整分析。

- 判断目标人群、核心暴露/特征/表型、比较对象和结局是否能被可靠表示。
- 区分 `verified`、`schema-supported`、`assumed` 和 `unknown`；不要把“理论可链接”写成“当前可执行”。
- 用最小汇总审计核对 cohort count、独立患者数、核心暴露覆盖、主要事件数和关键变量覆盖。未运行审计时不得编造数值。
- 只检查明显致命问题：核心构念不可测、长期结局不在数据范围、样本/事件明显不足、无法修复的时间倒置、治疗策略不可区分、严重适应证混杂或缺乏基本 overlap。
- 判断 notes、CXR、waveforms、基因组、长期随访或外部验证是否为回答问题的必要条件；缺少时明确降级、重构或否决。

关键构念与最低汇总证据均已支持时使用 `FEASIBLE`；schema 支持但样本、事件或覆盖未知时使用 `AUDIT_REQUIRED`；需要改变人群、暴露、结局或数据源时使用 `REDESIGN`；当前数据无法回答核心问题时使用 `NOT_FEASIBLE`。

默认使用 MIMIC-IV 3.1，除非用户指定其他版本。MIMIC-IV 3.x 的 `patients` 与 `admissions` 位于 `hosp`。对 derived schema、额外模块和外部数据，保留用户实际验证的名称与版本证据，不凭记忆强制改写。

临床价值不能把 `NOT_FEASIBLE` 的题目从总分中救回来；只能重构问题或更换数据源。

## 第三层：做出来能发表到哪里

把发表潜力作为前两层证据的结果，不单独凭感觉打分。综合判断：

- 创新是重复、增量还是实质性贡献；
- 是否解决清晰的临床决策或重要知识缺口；
- 核心构念和结局的可信度；
- 单中心 MIMIC 证据能够支持的推断强度；
- 是否具备独立验证、跨数据库复现或其他提升可推广性的路径；
- 与目标期刊当前 scope 和 article type 的契合度。

输出：

- `current_ceiling`：当前最多适合的证据层级或期刊家族，例如探索性、一般专科、较强专科或高影响潜力；
- `ceiling_blockers`：限制上限的核心问题；
- `upgrade_path`：最可能提高上限的证据，而不是堆砌分析；
- `confidence`：判断依据及不确定性。

用户指定期刊、分区或影响因子时，核验当前期刊范围、文章类型和分区来源；需要独立投稿定位复核时调用 `journal-reviewer`。不得保证一区、影响因子、录用或给出无可靠分母的投稿成功率。明确区分“选题阶段的潜力”与“完成分析后的可发表性”。MIMIC-only 预测研究若无独立验证，不得声称已证明临床效用或可推广性。

## 排序与决策

按顺序门禁排序，不使用一个总分掩盖致命缺陷：

1. 第一层不过，不进入可行性细化。
2. 第二层不可做，不因临床重要而上调。
3. 第三层只在值得且至少可审计的候选题之间比较。

优先给出 3-5 个不凑数的候选题；如果只有一个题达到门槛，就只推荐一个。最终动作使用 `advance_to_audit`、`reframe`、`park` 或 `drop`。

只有完成最近似文献核验且最低可行性审计通过后，才可建议进入 protocol/SAP；在此之前使用 `EVIDENCE_PENDING` 或 `AUDIT_REQUIRED`，不要写成已证实可做。

## 输出格式

先给最推荐题目和排序理由。然后对每个候选题分别输出：

1. working title 与一句话研究问题；
2. **值不值得做**：分别给出创新性、`contribution_path`、临床价值及其证据与状态，再给出综合 `worth_status` 和置信度；
3. **能不能做**：必须的数据元素、已知证据与未知项、最小汇总审计、致命风险、状态与置信度；
4. **做出来能发表到哪里**：贡献类型、`current_ceiling`、阻断项、升级路径与置信度；
5. 最终动作、为什么现在推进或放弃、下一步 skill。

在末尾列出尚未核验的关键假设。

## 常见误判

- **技术替换冒充创新**：换算法、加入 SHAP、新 cutoff、便利亚组或重新组合常见指标，本身不构成实质创新。
- **疾病重要冒充题目有价值**：严重结局不能替代明确的临床决策或知识后果。
- **未经检索确认创新**：未完成最近似 MIMIC 与非 MIMIC 文献核验时，不得标记 `substantive`。
- **把“没搜到”当作证据空白**：单一数据库、单一 query、前几条结果或搜索摘要不足以支持 `fill_gap`。
- **把可链接当成可执行**：额外模态、长期随访或外部数据没有版本、权限和覆盖证据时，保持未知或不可行。
- **过早承诺高发表上限**：单中心 MIMIC 证据、特别是无独立验证的预测研究，不能证明临床效用或可推广性。
- **选题阶段过度设计**：不要输出详细 eligibility/index/assignment/follow-up 契约、DCA、敏感性分析、统计代码或 expected tables/figures。

## 轻量设计分流

- Prediction：只确认目标使用者、决策时点、当前 comparator，以及性能改善是否可能改变行动；把 calibration、DCA、resampling 和 leakage plan 路由到 `mimic-prediction-modeling`。
- Phenotyping：只确认表型能回答什么临床/科学问题、核心变量能否获取；把特征窗、缺失处理、稳定性和命名规则路由到 `mimic-phenotyping-pipeline`。
- Treatment effect：只确认策略、比较对象和核心结局是否可区分，并筛查明显不可识别问题；把 target trial、IV/RD/DiD/ITS 假设与诊断路由到 `mimic-causal-analysis-guardrails`。
- Descriptive/association：要求明确超出常识性关联的知识后果；把模型和统计计划路由到 `mimic-statistical-analysis`。

选定题目后，使用 `mimic-cohort-builder` 与 `mimic-bigquery-qc` 完成最低可行性审计，再用 `mimic-study-protocol-sap` 冻结正式方案。涉及 codebook、暴露/结局、外部验证或完整流程时，分别路由到对应 specialist 或 `mimic-study-orchestrator`。
