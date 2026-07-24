---
name: mimic-data-governance
description: Enforce MIMIC and PhysioNet data-governance gates before reading files, scanning a workspace, invoking an AI model or external service, publishing results, or sharing derived data and models. Use for classifying MIMIC artifacts, checking DUA and authorized-user boundaries, deciding whether local or cloud processing may proceed, documenting zero-retention/no-training/no-human-review evidence, preventing disclosure, and planning compliant code or result release.
---

# MIMIC Data Governance

把治理检查放在任何内容读取、工作区扫描、模型调用或公开发布之前。默认本地处理；只在证据充分且机构要求允许时使用外部服务。无法确认数据类别、访问资格或服务行为时，停止处理受限内容，不要用猜测补齐合规结论。

## 审查操作与统一回执

由 `mimic-review` 调用或输入声明 `operation: audit` 时，本 skill 是只读 `governance` pass：

- 只审查明确列出的路径、metadata、政策证据和处理目的；不扩大扫描、不改变权限、不上传内容，也不修复研究文件。
- 使用同一 `review_run_id` 与 `input_hashes`，按 `../mimic-review/assets/templates/review-pass-receipt.yaml` 返回 `pass_id: governance`。
- `coverage_status` 仅用 `assessed | not-assessed`；`recommendation` 仅用 `proceed | revise | redesign | not-assessable`。
- finding 使用模板中的 canonical severity、status、stage、domain 与 `gate_effect`；缺少政策或范围证据必须记为 `not-assessed`，不能把治理决定写成含混的“pass”。
- 治理决定和 review receipt 同时返回；决定控制允许读取的范围，receipt 记录本次审查证据，二者不可互相替代。

## 执行门禁

1. **限定范围**：记录任务目的、拟读取的路径、拟调用的工具、数据来源和预期输出。只处理完成任务所需的最小范围。
2. **先做元数据盘点**：内容读取前只查看必要的文件名、扩展名、位置和大小；排除数据目录、导出文件、模型产物、日志、缓存、临时文件、凭据和版本控制历史。路径本身含患者信息时也按受限内容处理。
3. **确认授权**：确认操作者对涉及的每个 PhysioNet 项目拥有当前有效的个人访问资格、培训和 DUA。团队成员必须各自获权；共享账号或转交数据均不能通过。
4. **分类产物**：按 `references/classification-and-service-gate.md` 将输入和预计输出分类。无法分类时按受限级别处理。
5. **评估处理环境**：识别数据会到达的每个位置，包括 prompt、附件、日志、遥测、缓存、备份、人工审阅队列和子处理方。
6. **作出决定**：仅输出 `PROCEED_LOCAL`、`PROCEED_APPROVED_SERVICE`、`PROCEED_PUBLIC_ONLY` 或 `BLOCKED`。不得以“已去标识”替代 DUA 检查。
7. **最小化执行**：获得允许后只读取必要文件，避免打印患者级内容，并让中间产物继承输入中的最高敏感级别。
8. **发布前复核**：分别审查论文汇总结果、代码、模型和衍生数据；公开代码义务不等于允许公开数据或模型。

对每条具有约束力的政策或服务证据，记录来源、版本或发布日期、内容 hash、核验时间、复核或到期时间及适用账户/区域。只记录一个链接或产品名称不构成当前证据。汇总结果的披露阈值必须服从当前 DUA、机构政策和披露审查；本 skill 不规定一个可跨机构通用的小单元格阈值。

## 工作区扫描规则

- 自动扫描前先运行本门禁；治理检查不能从“先读全部文件再判断”开始。
- 请求用户提供数据来源和分类声明，或从仓库内明确的治理清单获取；没有声明时只允许扫描明显公开的代码、配置模板和文档骨架。
- 使用路径允许列表，不使用整个 home 目录或无边界递归扫描。默认排除 `.git/`、`.env*`、凭据、数据缓存、notebook 输出、日志、模型权重、嵌入、向量库和患者级导出。
- 将 SQL 代码与查询结果分开分类：不含真实值的 SQL 通常可公开，内联样例、查询缓存和结果文件可能受限。
- 不在报告中复制受限原文。只报告类别、位置、风险和所需整改；文件名本身敏感时使用代号。

## 外部服务判定

优先使用由授权研究者控制的本地环境。本地环境仍须具备访问控制、加密、最小权限、受控备份和安全删除。

仅当以下项目均有当前、可审计的证据，且机构政策或审批不禁止时，才判定外部服务可用于受限内容：

- 对输入、输出、日志、缓存、备份和滥用监控实行 zero data retention；
- 不用数据训练、改进或评估模型；
- 不进行人工审阅；
- 子处理方和数据地域在授权范围内；
- 研究者有权接受相应合同条款，且配置已在本次项目账户上生效；
- 服务政策、配置证据、核验日期和复核日期均已记录。

营销页、消费者隐私开关、未验证的“企业版”标签或口头承诺都不构成充分证据。任一项未知时输出 `BLOCKED`，并提供本地执行、只传公开代码、合成数据替代或人工脱敏摘要等安全路径。

## 输出契约

每次门禁输出以下字段：

```yaml
governance_decision: PROCEED_LOCAL | PROCEED_APPROVED_SERVICE | PROCEED_PUBLIC_ONLY | BLOCKED
scope: "要读取的明确路径和要执行的操作"
data_classes: []
source_projects_and_versions: []
authorized_user_confirmed: false
processing_destinations: []
service_evidence:
  source: null
  version_or_date: null
  sha256: null
  zero_retention: unknown
  no_training: unknown
  no_human_review: unknown
  subprocessors_and_region: unknown
  verified_on: null
  expires_or_review_on: null
controls: []
excluded_paths: []
release_plan: "代码、汇总结果、数据和模型分别说明"
blockers: []
next_review_date: null
```

不要把 `unknown` 自动转换为 `true`。输出决定前读取 `references/classification-and-service-gate.md`；项目级最低要求见根目录 `DATA_GOVERNANCE.md`。

## 发布与引用

- 对公开传播的研究结果，准备开放的可复现代码，但不得把凭据、患者级值、受限样例或查询结果提交到公开仓库。
- 将从 MIMIC 产生的数据集、嵌入、标注和模型视为敏感资源；若要共享，按 PhysioNet 当前衍生资源指引在与来源相同的受控协议下提交，不自行发布到普通公共托管平台。
- 在论文和代码文档中准确引用 PhysioNet、每个来源项目及其精确版本；记录数据提取日期、代码版本和衍生构建版本。
- 发布前重新核验 DUA、PhysioNet 指引、机构政策和服务条款；政策会变化，本 skill 不能替代机构审查或法律意见。
