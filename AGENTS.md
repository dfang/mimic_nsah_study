# AGENTS.md

## 项目背景

本仓库服务于以下研究：

**Early Multimodal Physiological Phenotypes and Outcomes in Critically Ill Patients with Non-traumatic SAH Using MIMIC-IV**
**使用 MIMIC-IV 识别重症非创伤性蛛网膜下腔出血患者的早期多模态生理表型及结局**

项目当前目标是从 MIMIC-IV 中提取非创伤性蛛网膜下腔出血（non-traumatic SAH）重症患者队列，构建 0-48 小时早期多模态生理特征，并使用可复现的无监督学习与回归流程分析临床表型、贫血/红细胞输血相关特征和结局。

既往 aSAH 研究脚本与中间结果需要保留，作为敏感性分析或后续回到 aSAH 主题时复用。

## 数据与临床范围

- 主要数据源：BigQuery 上的 MIMIC-IV 3.1。
- 预期源数据集：
  - `physionet-data.mimiciv_3_1_hosp`
  - `physionet-data.mimiciv_3_1_icu`
  - `physionet-data.mimiciv_3_1_derived`
- 本研究使用的 BigQuery 项目名：`mimic-study-498508`。
- 既往 aSAH 研究数据集名：`asah_study`。
- 当前 non-traumatic SAH 主研究数据集名：`non_traumatic_sah_study`。
- `mimic-study-498508.asah_study` 用于保留上次 aSAH cohort 构建过程中的中间结果表和最终分析表。
- `mimic-study-498508.non_traumatic_sah_study` 用于当前 non-traumatic SAH cohort 中间结果、最终宽表和分析结果。
- 当前研究队列：成年 non-traumatic SAH 重症患者，需有 ICU 住院记录；不要求动脉瘤诊断或动脉瘤处置证据。
- 动脉瘤诊断和动脉瘤处置证据应保留为分层或敏感性分析变量。
- 核心暴露/分层因素：早期贫血、红细胞输血、循环/呼吸/神经/肾功能等早期生理表型。
- 核心结局：住院死亡率；在数据可得时，可纳入 ICU 死亡、住院/ICU 时长等次要结局。
- 主要分析目标：识别 non-traumatic SAH 的早期临床表型及其结局差异；如进行治疗效应分析，应明确其探索性和因果假设。

## 仓库约定

- 分析代码应尽量保证从干净 checkout 后可复现、可执行。
- 优先使用显式 SQL 和 Python 脚本，不要把关键逻辑只隐藏在 notebook 中。
- 除非用户明确要求，不要将生成数据、凭据、本地导出文件或大型结果文件提交到 git。
- 流水线文件建议使用清晰的阶段编号，例如：
  - `01_create_dataset.sql`
  - `02_transfusion_grouping.py`
  - `03_causal_ml_analysis.py`
  - `run_all.sh`
- 除非任务明确要求修改，保留 `option1/` 和 `option2/` 中已有研究资料。
- 生成内容到 `dist/` 时，必须放入 `YYYYMMDD`（如 `20260702`）文件夹内，并且在该目录下编写一个 `readme.txt`，明确告知其中的 markdown 和 pdf 文件是由哪个模型（如 `codex`、`gemini` 或 `claude`）生成的。


## BigQuery 与 SQL 规范

- 除非用户明确切换数据库版本，默认使用 MIMIC-IV 3.1 表名。
- 完整 BigQuery 表名必须使用反引号包裹。
- 早期生理指标优先使用 `physionet-data.mimiciv_3_1_derived` 的社区衍生表
  （如 `vitalsign`, `gcs`, `bg`, `chemistry`, `complete_blood_count`），再用 `hosp`/`icu`
  原始表作为兜底或审计来源；这样可减少手工 itemid 映射遗漏和指标缺失。
- 派生分析表默认可使用 `CREATE OR REPLACE TABLE`；如果任务明确要求，则先写 `DROP TABLE IF EXISTS`。
- 每个队列构建步骤应添加简洁注释，说明目的。
- 所有基线协变量必须在索引时间点 `T0` 之前提取。
- 时间戳逻辑是因果设计的一部分；不要随意移动暴露、协变量或结局窗口。如需调整，必须记录理由。
- 对生命体征和实验室指标应用临床合理范围过滤。
- 旧 aSAH 脚本默认使用 `mimic-study-498508.asah_study`。
- 新 non-traumatic SAH 脚本默认使用 `mimic-study-498508.non_traumatic_sah_study`。
- 如果需要保留旧 `ash_study` 结果，先运行 `00_migrate_ash_study_to_asah_study.sql` 复制到 `asah_study`，确认无误前不要删除旧 dataset。
- 不要将其他私人 BigQuery 项目 ID 硬编码到代码中，除非用户明确提供。

## 因果分析规范

- 将队列构建、治疗分组、预处理、建模和报告分成清晰阶段。
- 设置随机种子，保证结果可复现。
- 根据估计器要求使用训练/测试划分、交叉拟合或其他必要验证策略。
- 在模型支持时，报告 CATE/ATE 估计的不确定性。
- 不要在证据不足时宣称已经确认 HTE；应区分探索性亚组信号和经验证的治疗效应修饰。
- 在注释或报告中记录关于混杂、阳性假设、缺失值和结局定义的关键假设。

## 隐私与合规

- 不要提交 MIMIC 凭据文件、服务账号密钥、下载的患者级数据或任何 PHI。
- MIMIC 已去标识化，但逐行临床数据仍需谨慎处理。
- 优先保留可复现的提取脚本和汇总结果，避免提交本地患者级导出。

## 验证要求

在声明完成前：

- 在可行时，检查已修改脚本是否存在语法或格式错误。
- 对 SQL，检查表版本是否一致、时间窗口是否符合设计、队列连接键是否正确。
- 对 Python，在依赖或数据访问不可用时，至少运行轻量级语法检查。
- 如果因缺少 BigQuery 凭据、源数据或可选建模依赖而未运行某些分析步骤，必须明确说明。
