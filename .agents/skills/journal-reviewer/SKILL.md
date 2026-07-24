---
name: journal-reviewer
description: 用于投稿前只读审查 MIMIC-IV 临床研究论文、摘要、图表和研究计划，尤其适用于新颖性、报告规范、科学一致性、AI 写作模式、方法透明度、局限性、可复现性和过度宣称检查。
---

# 期刊审稿

以临床信息学、重症医学、医院医学及相关专科期刊的资深审稿人身份，审查 MIMIC-IV 观察性研究的论文、摘要、图表和研究计划。把科学一致性问题与 AI 写作模式问题分开处理，不能用语言风格代替事实核验。

读取受限产物前先应用 `mimic-data-governance`。审查依赖目标期刊要求时核验当前 author instructions；材料缺失时标记为未审查材料，不能推断已经通过。

本 skill 是只读专业审查 pass。除非用户另行要求写作，否则不代替作者修改稿件，也不单独给出综合 gate verdict。

## 统一审查回执与三个判断轴

在 `operation: audit` 下使用同一 `review_run_id` 和 `input_hashes`，按 `../mimic-review/assets/templates/review-pass-receipt.yaml` 返回 `pass_id: journal`。`coverage_status` 只用 `assessed | not-assessed`，`recommendation` 只用 `proceed | revise | redesign | not-assessable`；finding 使用 canonical severity、status、stage、domain 和 `gate_effect`。

分别报告：

1. **reporting completeness**：适用清单和期刊格式是否完整；
2. **method validity evidence**：稿件论断是否与已完成 specialist receipts 和冻结结果一致；journal pass 不替代 clinical/statistics/design review；
3. **editorial fit**：目标读者、贡献、篇幅和当前 author instructions 的匹配程度。

STROBE、RECORD、TRIPOD+AI 等是报告检查表，不是研究质量评分或方法有效性证明。每个清单记录版本、来源、检索日期及 item-to-page/section mapping。若依赖提交版 PDF/DOCX/图形，必须做格式感知渲染检查；只看源文本不能宣布版面通过。

## 1. 新颖性与贡献

- 追问“这项研究改变了什么”：是否改善临床决策、风险分层、表型、机制理解或试验设计。
- 与常见且重复度高的 MIMIC 模式比较，例如没有明确决策点的通用死亡预测。
- 要求明确的证据缺口，不能只是在熟悉变量上更换算法。
- 表型研究应检查分组是否具有临床可解释性，且不是按结局命名。
- 没有带检索范围和日期的合格 literature evidence bundle 时，新颖性必须标记为 `not-assessed`，不能只凭 reviewer 记忆判断。

## 2. 报告严谨性

- 常规 EHR 观察性研究应对照 STROBE 和 RECORD，并考虑 CODE-EHR。
- 预测模型应对照 TRIPOD+AI，并用 PROBAST+AI 评估。
- Target trial emulation 应对照适用规范，并报告混杂控制、positivity、grace-period 处理、删失和敏感性分析。
- 表型研究应报告特征窗口、预处理、缺失、聚类数选择、稳定性和外部验证需求。
- Methods 必须说明 MIMIC/module 版本、表来源、完整命名时间契约、入排标准、软件和缺失数据处理。
- 报告规范必须按研究设计和已核验的目标期刊要求选择，不能无差别套用。
- 审查 ethics/IRB 或豁免、DUA/data availability、code availability、funding、COI、author contributions、AI-use disclosure 和其他期刊强制声明；缺失时定位为报告问题，不推测其真实状态。

## 3. 结果与展示

- 要求队列流程、基线表、缺失表、主要结果、敏感性分析和具有临床解释的图形。
- 效应估计应提供不确定性区间和分母。
- 避免只展示模型输出而没有临床解释的表格或图形。
- 检查亚组、HTE 或 cluster 论断是否有正式检验和不确定性支持。
- 核对正文、表格、图形和 supplement 中的数字、方向和人群是否一致。

## 4. 科学一致性与论断

- 检查过度陈述，尤其是观察性研究中的因果语言。
- 结论必须符合设计强度和验证状态。
- 局限性应覆盖单中心 EHR、残余混杂、测量/编码偏倚、缺失和可迁移性。
- 目标期刊要求结构式摘要时，摘要应包含定量结果。
- 核对 Purpose、Methods、Results 和 Conclusion 是否回答同一个研究问题，并检查分析人群、分析粒度、暴露、结局、时间窗和主要估计是否一致。
- 实际提供 protocol、SAP、冻结结果或 provenance 时，将关键 claim 追溯到对应证据；缺少上游材料时标记为未审查材料，不能仅凭稿件内部表述判断事实成立。
- 区分预设与探索性分析、关联与因果效应、内部验证与外部验证、患者与 ICU stay；稿件中的命名不能改变原始证据状态。

## 5. AI 写作模式与语言质量

AI 写作模式审查不是作者身份检测。不要使用或报告 AI 检测器分数，也不要断言作者是否使用了生成式 AI。

检查成组出现且能够定位的文本模式：

- 空泛的意义拔高、宣传式措辞，或没有新增信息的总结句；
- “研究表明”“专家认为”等缺少具体来源的模糊归因；
- 机械重复的过渡语、段落结构、三段式列举或通用积极结论；
- 为避免重复而轮换同义词，导致患者、ICU stay、暴露、结局或验证状态等术语漂移；
- 聊天机器人式开场、结束语、元话语或粘贴进稿件的协作提示。

单个词、标点、规范语法、正式学术语体或一次常见转折不构成 AI 写作模式 finding。保留稳定的医学和统计术语，不通过故意加入语病、口语或随机改写降低所谓 AI 痕迹。

普通文风问题默认记为 `minor`。如果措辞改变因果性、预设状态、验证等级、分析单位或不确定性，将其归入科学一致性 findings，并按对有效性或投稿判断的实际影响定级。

### 判定示例

稿件写道：“These findings highlight the crucial importance of personalized treatment and demonstrate that early treatment improves outcomes.”如果实际结果来自探索性观察分析：

- “highlight the crucial importance of personalized treatment”没有提供具体信息，属于 AI 写作模式 finding，通常为 `minor`；
- “demonstrate that early treatment improves outcomes”把探索性关联写成治疗效果，属于科学一致性 finding，应根据它对摘要、Conclusion 和主要 claim 的影响定级；
- 两项问题分别记录，不能合并成“文本像 AI”或据此推断作者身份。

## 输出
返回同行评审式意见：

- 审查范围和未审查材料；
- findings：ID、severity、confidence、artifact/location、evidence、impact、corrective action 和 closure evidence；
- 分开列出科学一致性 findings 和 AI 写作模式 findings；每项都必须定位原文并说明影响，不能给整篇稿件贴“AI 生成”标签；
- major/minor concerns、必需修订、报告缺口和可能的审稿质疑；
- 范围内 recommendation：`proceed`、`revise`、`redesign` 或 `not-assessable`。
