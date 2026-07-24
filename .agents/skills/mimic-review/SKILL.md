---
name: mimic-review
description: 对 MIMIC 研究、protocol、SQL 流水线、统计分析、模型、论文或工作区执行独立、证据可追溯的综合审查。用于 focused 专项审查、正式 lifecycle gate、投稿准备度评估、跨学科质量控制、阻塞问题分诊，以及临床、统计、SQL、复现和期刊审查的统一汇总。
---

# MIMIC 综合审查

将本 skill 作为 `operation: audit` 的只读审查门禁。它只产出输入快照、pass receipts、coverage、findings 和 verdict；不得修复、训练、查询写入、冻结、打包或发布研究产物。需要整改时结束本次 review run，由 builder 在新任务中修改，再创建新快照复审。

`references/review-pass-registry.json` 是 pass ID、skill、依赖、输入角色、适用性和 gate 路由的 machine-readable authority。Predicate 只能读取 registry `predicate_dsl.routing_context.fields` 声明且存在于 `review-input.yaml` 的字段；`artifacts.role` 按声明规则投影 artifacts 数组中每个对象的 `role`，其他未知或缺失字段不匹配。不要凭记忆复制 specialist 标准；每次审查都读取 registry、当前 specialist `SKILL.md` 和 `assets/templates/review-pass-receipt.yaml`。

## 1. 先解析审查模式

使用以下逻辑请求，不要宣称仓库已经提供 `mimic-review --perspectives` CLI：

```yaml
mode: focused | gate
gate: null # gate 模式必须使用 canonical lifecycle stage
operation: audit
requested_passes:
  - statistics
input_snapshot: path/to/review-input.yaml
```

允许的 `requested_passes`：

- `governance`
- `protocol-time`
- `sql-data`
- `clinical`
- `statistics`
- `prediction`
- `causal`
- `phenotyping`
- `external-validation`
- `evidence-novelty`
- `journal`
- `reproducibility`
- `design-specific`
- `all`

前 12 项是 registry 中的 canonical pass IDs；`design-specific` 和 `all` 是 registry 显式声明的 aliases。`all` 只表示当前范围内所有适用 pass。`design-specific` 必须按 registry 的 `study.design_family` mapping 解析为 prediction、causal 或 phenotyping pass；字段缺失、冲突或没有 mapping 时 fail closed，不能猜测。

按以下规则解析：

- `focused`：必须有至少一个 requested pass；运行这些 pass、其 dependency passes 以及 governance；只返回范围内 recommendation。
- `gate`：必须声明 canonical gate；根据 stage contract、manifest、design family 和 subtype 推导全部 required passes；requested passes 只能增加审查，不能关闭必需 pass。
- 用户明确要求“只审临床”“重点审统计”等窄范围问题时，可解析为 `focused`。
- 用户要求综合审计、阶段通过、publication readiness 或 `READY/REVISE/REDESIGN` 时，必须解析为 `gate`。
- 模式、gate 或 pass 含糊时先要求澄清；未知 pass、无效 gate 或冲突配置必须 fail closed。
- governance 和范围确定始终执行，不能由用户关闭。
- `manuscript_review` 至少要求 governance、clinical、statistics、journal 和 reproducibility；clinical/statistics 缺少材料时必须保留 required 行并标记 `not-assessed`，不得写成 `not_applicable`。

focused 模式不产生综合 gate verdict。需要正式 readiness 判断时，必须建立新的 gate review run。

## 2. 治理与工作区访问

扫描或读取研究文件前先应用 `mimic-data-governance`。未经验证的外部环境不得打开患者级表格、notes、images、衍生数据集、模型权重或不安全的小单元格输出。

治理证据不足时，只审查非敏感 protocol、SQL 文本、schema、聚合安全报告和论文文本；其他材料标记为 `not-assessed`。

优先使用 study manifest 或用户明确提供的文件列表。两者都不存在时：

1. 只列候选文件 metadata，不读取内容。
2. 排除 `.git/`、`.omx/`、环境、缓存、依赖、raw-data 目录、模型权重、生成二进制和本 skills 库自身文档。
3. 按敏感性和研究阶段分类。
4. 只读取最小的、治理批准的范围。

PDF、DOCX 和图形必须使用格式感知的渲染与检查流程；只看文件名不构成审查。

## 3. 建立不可变输入快照

治理通过后，从 `assets/templates/review-input.yaml` 创建本次审查输入。至少记录：

```yaml
review_run_id: "<stable id>"
created_at: "<ISO 8601>"
operation: audit
repository:
  identity: "<repository identity>"
  commit: "<git commit>"
  dirty_state: true
artifacts:
  - role: protocol
    path: path/to/protocol.md
    version: "1.0"
    sha256: "<sha256>"
```

stage artifact 是 bundle index 时，必须：

1. 核对 index 与 stage `sha256`。
2. 展开全部成员。
3. 验证每个 member hash。
4. 对当前 gate 所需成员进行内容审查。
5. 在 coverage matrix 中逐项记录 `assessed` 或 `not-assessed`。

所有 pass 必须接收相同的 `review_run_id` 和 artifact hashes。工作区内容变化后创建新的 review run；不同快照的 findings 不得合并成一次通过结论。

## 4. 解析并加载当前 specialist passes

在应用每个 pass 前完整读取对应 `SKILL.md`，记录 skill 版本或 commit、reviewer identity 和实际收到的 artifact hashes。

### Gate 模式

1. 根据 `references/review-pass-registry.json`、`skills/mimic-study-orchestrator/references/stage-contracts.md` 和 manifest 推导 required passes。
2. 必需 artifact 缺失时仍保留对应 coverage 行并标记 `not-assessed`，不能通过未发现文件跳过。
3. protocol/time：`mimic-study-protocol-sap`。
4. SQL/data：`mimic-bigquery-qc`。
5. clinical：`clinical-reviewer`。
6. statistics：`statistics-reviewer`。
7. prediction：`mimic-prediction-modeling` 加 `statistics-reviewer`。
8. causal/HTE：`mimic-causal-analysis-guardrails`，按 target trial、IV、RD、DiD 或 ITS subtype 审查。
9. phenotyping：`mimic-phenotyping-pipeline`。
10. external validation：`mimic-external-validation`。
11. manuscript/reporting：`journal-reviewer` 和适用报告规范。
12. reproducibility/release：`mimic-reproducibility-release`。

每个 specialist 都必须收到 `operation: audit`。任何要求修复、重训、执行写入查询、补搜、改稿、冻结或打包的回复都违反 pass contract，不能进入汇总。

### Focused 模式

只运行 requested passes、对应 specialist contract 声明的 dependency passes 和 governance。对已知适用但未请求的领域记录 `required=false`、`requested=false`、`status=not-assessed`，不得扩展为完整 gate review。

治理、范围确定和输入快照必须先完成；其他无依赖 pass 可以顺序或并行运行，但必须使用同一个不可变快照。

## 5. 验证 specialist receipt

每个 pass 必须从 `assets/templates/review-pass-receipt.yaml` 返回完整回执。`findings` 必须内嵌完整 canonical finding objects，不得用 finding ID、链接或单独列表代替：

- `review_run_id`、`pass_id`、`reviewer_identity`、`skill_version`、`input_hashes`
- `coverage_status`、`coverage_notes`、`recommendation`、`findings`

汇总前逐项检查：

1. `pass_id` 存在于 registry 且 skill 路由一致；
2. operation 是 audit，reviewer identity 与作者/builder 独立；
3. review run 和每个 artifact hash 与输入快照完全一致；
4. coverage、recommendation、severity、status、stage、domain 和 `gate_effect` 只使用模板词表；
5. finding 有 artifact/location、evidence、risk、recommended action、owner、verification 和 closure 字段；
6. `resolved`/`accepted-risk` 有完整 closure evidence；未审查材料没有被写成通过。

不规范 receipt 先标为该 pass `not-assessed` 并记录合同 finding；不得静默修补 specialist 输出后当作有效证据。

## 6. 文献、指南和报告规范证据

- novelty 或与既有研究的比较只有在提供带数据库、检索式、范围和日期的 literature evidence bundle 时才能标记为 `assessed`。
- 需要补建或更新证据时使用 `mimic-literature-evidence`；窄检索不能冒充系统综述级完整证据。
- 缺少合格文献证据时，journal pass 仍可审查结构、写作和 claims，但 novelty 必须标记为 `not-assessed`。
- 临床定义依赖指南时，记录来源、版本或发布日期及核验日期；不能只凭 reviewer 记忆宣称符合权威指南。
- 报告规范根据设计条件选择。依赖目标期刊要求时，记录 live author instructions 的来源和核验日期。

## 7. Coverage matrix

判断 readiness 前建立 coverage matrix。每行必须包含：

- `domain`
- `artifacts`
- `reviewer`
- `required`
- `requested`
- `applicability`
- `status`
- `input_hashes`

`applicability` 使用 `applicable`、`not_applicable` 或 `undetermined`；`not_applicable` 必须有证据。`status` 使用 `assessed` 或 `not-assessed`。`not_applicable` 是 coverage 属性，不是 finding status。

至少覆盖：

| Domain | Reviewer |
|---|---|
| governance | `mimic-data-governance` |
| protocol/time | `mimic-study-protocol-sap` |
| SQL/data | `mimic-bigquery-qc` |
| clinical | `clinical-reviewer` |
| statistics | `statistics-reviewer` |
| design | prediction、causal 或 phenotyping specialist |
| validation | `mimic-external-validation` |
| evidence/novelty | `mimic-literature-evidence` |
| reporting | `journal-reviewer` |
| reproducibility | `mimic-reproducibility-release` |

## 8. 可追溯 issue register

每个 finding 使用 canonical schema：

```yaml
id: REV-001
severity: blocking | major | minor | note
gate_effect: blocks_ready | requires_redesign | none
confidence: high | medium | low
stage: question | protocol | concepts | cohort | features | analysis | validation | analysis_review | manuscript | manuscript_review | release | submission
domain: governance | design | data | clinical | statistics | reporting | reproducibility
artifact: path
location: line, query block, table, figure, or section
evidence: observed fact
risk: validity or publication consequence
recommended_action: smallest verifiable correction
owner: responsible role
verification: evidence required to close
status: open | resolved | accepted-risk | not-assessed
closure_evidence: null
closed_by: null
closed_at: null
```

不要报告没有证据位置的模糊担忧。Builder/Author findings 与 independent reviewer findings 分开保存。同一底层问题和修正动作完全相同时才允许去重；保留最高 severity、全部 evidence locations 和贡献 reviewers。

`resolved` 必须填写 `closure_evidence`、`closed_by` 和 `closed_at`；`accepted-risk` 必须在 closure evidence 中记录授权责任人。修正后的产物形成新快照并重新送审，不能直接改写旧 finding 获得通过。

## 9. Verdict

focused 模式只返回各 pass 的范围内 recommendation，不返回 gate verdict。

gate 模式按固定优先级聚合：

1. 任一 required/applicable pass 为 `not-assessed`、applicability 未定或 receipt 无效：`NOT_ASSESSABLE`。
2. coverage 完整且任一 open finding 为 `gate_effect: requires_redesign`：`REDESIGN`。
3. coverage 完整、无需 redesign，但任一 open finding 为 `gate_effect: blocks_ready`，或 severity 为 blocking/major：`REVISE`。
4. coverage 完整，且没有 open `blocks_ready`、blocking 或 major finding：`READY`。

`NOT_ASSESSABLE` 时仍报告已经观察到的有效 findings，并单列 `observed_gate_effects`；缺失 coverage 不能隐藏已经确认的 redesign 风险，但最终 verdict 仍保持 `NOT_ASSESSABLE`。`READY` 只代表通过声明的当前 gate，不表示期刊必然接收。

## 10. 输出结构

返回：

1. `review_run_id`、mode、canonical gate、requested passes 和 required passes；
2. 治理模式、范围、输入快照、artifact hashes、已提供和排除材料；
3. coverage matrix；
4. gate 模式的 verdict，或 focused 模式的 pass-level recommendations；
5. 按下游影响排序的 blocking 和 major findings；
6. minor findings；
7. 去重后的行动计划、owner 和 verification evidence；
8. resolved findings；
9. `not-assessed` 领域和缺失材料；
10. 已验证的 specialist pass receipts、reviewer identity、skill 版本、实际输入 hashes 和无效 receipt 原因。
