# 数据分级与服务门禁

## 官方依据

执行时重新打开并核验当前版本：

- [Use of MIMIC Data with Large Language Models and Online Services](https://physionet.org/news/post/llm-responsible-use/)
- [PhysioNet Credentialed Health Data License / DUA 1.5.0](https://physionet.org/about/licenses/physionet-credentialed-health-data-license-150/)
- [PhysioNet credentialing and reuse FAQ](https://physionet.org/about/faqs/)
- [Guidance for derived MIMIC datasets and models](https://mimic.mit.edu/docs/community/derived/)
- [PhysioNet project publishing guidance](https://physionet.org/about/publish/)

PhysioNet 当前指引要求研究者对第三方服务的数据行为负责，推荐本地部署；云服务至少要核验 zero data retention、no training 和 no human review。它也要求将 MIMIC 衍生数据集和模型视为敏感资源。机构政策、伦理审批或数据出境规则可以比这里更严格。

## 分类

按输入和可推断输出中的最高等级分类。去标识的 MIMIC 仍是 credentialed/restricted data，不能降为公开数据。

| 类别 | 典型内容 | 默认处理 |
|---|---|---|
| `PUBLIC` | 不含真实患者值的代码、schema 名称、公开论文、空白模板、合成测试数据 | 可在普通开发工具中处理；仍检查凭据和许可证 |
| `AGGREGATE_REVIEW` | 经过披露审查的汇总表、统计量和图，不含小单元格、稀有组合或可追溯记录 | 仅在记录披露审查后用于写作/审查；不自动认定可公开 |
| `MIMIC_RESTRICTED` | 原始表、患者级行、notes、影像、波形、事件时间、ID、样例记录和查询结果 | 仅限授权研究者及获批受控环境；默认本地 |
| `DERIVED_SENSITIVE` | 患者级特征、标签、embedding、向量库、模型权重、梯度、检查点、合成数据、提示/输出日志 | 按 `MIMIC_RESTRICTED` 处理，直到正式披露评估证明可降级 |
| `SECRET` | PhysioNet 凭据、云密钥、服务账号、访问令牌、连接串 | 不得交给模型或写入报告/仓库；使用密钥管理器 |

以下情况不得自行降级：删除 `subject_id`；替换成随机 ID；只保留少量列；把患者行嵌入向量；模型“不能直接查看训练数据”；声称数据是 de-identified。聚合结果也可能因极小单元格、罕见诊断组合、极端时间线或可链接图表而泄露信息。

## 工作区内容读取前检查单

1. 记录任务和最小必要路径允许列表。
2. 确认路径是否来自 MIMIC、MIMIC-Note、MIMIC-CXR、MIMIC-ED、波形或其衍生资源，并记录精确版本。
3. 确认当前操作者和每位接收者均有相应项目的个人授权。
4. 只做本地元数据盘点；不预览文件内容，不生成缩略图，不索引，不上传。
5. 排除以下位置：
   - 数据与导出目录；
   - `.git/` 历史、stash 和大文件对象；
   - notebook cell outputs；
   - 日志、trace、crash dump、缓存和临时目录；
   - 权重、embedding、向量数据库和模型服务日志；
   - `.env*`、credential 文件、云配置和密钥。
6. 对每个允许路径标注类别；任何 `UNKNOWN` 按 `MIMIC_RESTRICTED` 处理。
7. 列出工具会发送或持久化的内容，包括文件内容、命令输出、错误堆栈和遥测。
8. 先输出治理决定，再开始读取。

## 服务证据表

为每个外部服务保存以下记录，不要只保存网页链接：

| 字段 | 所需证据 |
|---|---|
| 服务与具体产品 | 产品名、账户层级、区域、API/网页界面 |
| Zero retention | 输入、输出、日志、缓存、备份、滥用监控和故障排查均不保留的合同或正式文档 |
| No training | 不用于训练、微调、评估或产品改进的条款 |
| No human review | 无员工、承包商或标注人员查看的条款与实际配置 |
| 子处理与地域 | 子处理方清单、传输地域、跨境条件 |
| 项目配置 | 管理控制台证据、策略 ID 或机构批准记录 |
| 时效 | 核验日期、核验人、下一次复核日期、政策版本 |

任一关键字段缺失、相互矛盾或只对部分流量生效时，受限内容判定为 `BLOCKED`。把服务变更视为重新评估触发器。

## 输出与发布审查

分别判定四类产物：

1. **代码**：去除内联患者值、结果缓存、路径、project ID、密钥和受限样例；使用合成 fixture。公开传播研究结果时，按 DUA 准备开放代码仓库。
2. **论文汇总结果**：检查小单元格、罕见组合、个体时间线、图中散点、附录明细和可链接信息；遵守机构披露阈值。
3. **衍生数据**：默认敏感；通过 PhysioNet 受控发布流程和来源项目关系提交。
4. **模型**：模型权重、embedding、检查点和训练日志默认敏感；公开前需要记忆/重构风险评估，并按 PhysioNet 衍生模型指引发布。

发现疑似可识别信息时停止传播、保全最小必要证据并按当前 PhysioNet DUA 指定渠道报告；不要把内容复制进 issue、聊天或普通邮件。
