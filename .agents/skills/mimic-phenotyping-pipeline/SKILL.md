---
name: mimic-phenotyping-pipeline
description: Design and review MIMIC-IV unsupervised phenotyping pipelines. Use for early ICU multimodal feature tables, preprocessing, missingness handling, scaling, clustering, cluster-number selection, stability analysis, phenotype interpretation, outcome association, figures, and reproducible phenotype manuscripts.
---

# MIMIC Phenotyping Pipeline

用这个 skill 设计或审查 MIMIC-IV 无监督表型研究。目标不是“跑出几个 cluster”，而是得到稳定、可解释、可复现、与临床结局相关但不过度因果化的 phenotypes。

读取患者级特征前先应用 `mimic-data-governance`。将预处理、随机种子和表型分配规则交给 `mimic-reproducibility-release` 冻结和审计。

## 输入表要求

- 一行代表一个分析单元，通常是 `stay_id` 或 `hadm_id`。
- 必须包含可用的 `subject_id`、`hadm_id`、`stay_id` 以及命名清楚的 cohort entry、feature-window end 和 outcome follow-up times。
- 同一 `subject_id` 有多个 stay/admission 时，记录 repeat structure 和保留规则；不得把同一患者的记录拆到 discovery、replication 或 evaluation 分区。
- 特征列必须有清楚窗口和 summary，例如 `creatinine_max_0_48h`。
- outcome 和 downstream variables 不得进入 clustering feature set。
- outcome follow-up 必须从 feature window 结束之后开始；不能把窗口内事件同时当聚类输入和下游结局。
- 保留 missingness indicators 或 measurement counts。

## 预处理

- 先做临床范围过滤和极端值审查。
- 删除缺失过高或临床含义不稳定的变量，阈值要记录。
- imputation 方法要可复现，常见为 median/mode 或模型化填补。
- 连续变量 clustering 前通常需要 scaling。
- 高相关变量要考虑合并、删除或解释共线影响。

## 聚类与模型选择

可选方法：

- KMeans：简单、可解释，但依赖 scaling 和球形 cluster 假设。
- Gaussian mixture：允许概率分配，但假设更强。
- hierarchical clustering：适合可视化相似性，但大样本成本高。
- consensus/stability clustering：用于稳定性评估。

选择 cluster 数时综合：

- silhouette、Calinski-Harabasz、Davies-Bouldin。
- bootstrap stability / Jaccard similarity。
- cluster size 是否合理。
- 临床解释是否清晰。
- outcome gradient 是否存在但不是唯一依据。

## 稳定性分析

- 设置 random seed。
- 多 seed 重复聚类。
- bootstrap 或 subsampling 按能够保留依赖关系的最高单位分组（MIMIC 通常为 `subject_id`）评估 cluster membership 稳定性；不得把同一患者的多个 stay 当作独立重采样单位。
- 报告每个 cluster 的 size、核心特征、稳定性指标。
- 不稳定 cluster 不应被强行命名为明确临床表型。

## 解释与结局关联

- 使用 standardized feature profiles、heatmap、radar/forest plots 解释 cluster。
- 比较 baseline characteristics 时避免把聚类输入变量再次当成独立发现夸大。
- outcome association 可用 logistic/linear/Cox 回归，但表述为 association。
- 如果声称治疗效应异质性，需要另行使用因果分析护栏。

## 完成前检查

- outcome 没有泄漏进 clustering。
- preprocessing 和 random seed 可复现。
- cluster 数选择有多重证据。
- cluster 稳定性已检查。
- 重复 stay/admission 的 resampling 与分区按 subject 或更高依赖单位分组。
- 表型命名克制，避免过度临床化。
- manuscript 中明确探索性性质和外部验证需求。
