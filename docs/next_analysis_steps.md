# SQL 执行后下一步分析流程

SQL 已生成 cohort 中间表后，下一步不要马上写结论。先按以下顺序检查数据质量、导出宽表、运行聚类，再确认 K=3 主分型是否稳定、K=4 是否仅作为高分辨率探索亚型，以及是否能做贫血分层回归。

## 1. 先在 BigQuery 检查关键结果表

### 1.0 Derived schema 与来源贡献

运行 `10_create_non_traumatic_sah_cohort.sql` 时，脚本开头会先列出 `mimiciv_3_1_derived` 中关键表的可用字段。重点确认这些字段存在：

- `complete_blood_count`: `hemoglobin`, `platelet`
- `complete_blood_count`: `hematocrit`，用于 ePVS 候选变量
- `chemistry`: `creatinine`, `sodium`
- `gcs`: `gcs`, `gcsmotor`
- `vitalsign`: `heart_rate`, `sbp/sbp_ni`, `mbp/mbp_ni`, `spo2`
- `bg`: `lactate`, `po2`, `pao2fio2ratio`，仅用于描述/敏感性血气变量，不作为主聚类必需来源

如果主聚类字段缺失，先停下来改对应指标来源，不要继续使用空缺字段生成宽表。血气字段缺失不应阻断主聚类，但需要记录覆盖率。

### 1.1 Cohort flowchart

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.cohort_flowchart_counts`
ORDER BY step;
```

重点看：

- `07_primary_analysis_no_massive_transfusion` 是否仍有足够样本。
- `08_sensitivity_icu_los_ge_48h` 与主分析差距是否很大。
- `09_sensitivity_no_rbc_48h` 是否保留大部分样本。

### 1.2 核心变量缺失率

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.feature_missingness_summary`
ORDER BY missing_rate DESC;
```

判断：

- 单个核心变量缺失率 `<20%`：中位数填补可以接受。
- 单个核心变量缺失率 `20%-40%`：主分析可谨慎保留，但必须做敏感性分析。
- 单个核心变量缺失率 `>40%`：不建议直接作为主聚类变量，考虑替换或作为敏感性分析。

当前主聚类使用 8 个变量：`hb_min_48h_all`、`gcs_motor_min_48h`、`map_min_48h`、`shock_index_max_48h`、`spo2_min_48h`、`creatinine_max_48h`、`inr_max_48h`、`platelet_min_48h`。`sodium_max_48h`、`hb_min_48h_pre_transfusion`、`gcs_min_48h`、`gcs_grade_min_48h`、`lactate_max_48h`、`pao2_fio2_min_48h`、`spo2_fio2_min_48h` 和 `oxygenation_min_48h` 是描述或敏感性字段，不进入主聚类。

同时检查候选增强变量：

- `epvs_mean_48h_candidate`：若缺失率低、分布合理，可考虑敏感性聚类；不要和 Hb/Hct 的重复信息解释为独立生理维度。
- `troponin_peak_48h_candidate`：先看缺失率、assay label 和单位。若只在少数疑似心肌损伤患者中检测，建议作为描述/分层变量，不进入主聚类。
- `lactate_max_m6_48h_sensitivity` 和 `troponin_peak_m6_48h_candidate`：ICU 前 6 小时到后 48 小时窗口仅作预先定义的敏感性/描述窗口，不能和主 0-48h 核心聚类窗口混用。

乳酸缺失率在 `feature_missingness_summary` 中查看。血气/FiO2 氧合变量单独查看，但不作为主聚类纳入条件：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.oxygenation_source_missingness_summary`
ORDER BY missing_rate DESC;
```

重点比较 `pao2_fio2_min_48h`、`spo2_fio2_min_48h` 与 `oxygenation_min_48h` 的缺失率，用于说明为什么这些变量不进入主聚类。

肌钙蛋白 assay 单独查看：

```sql
SELECT
    troponin_label,
    valueuom,
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(troponin_value) AS min_value,
    APPROX_QUANTILES(troponin_value, 4)[OFFSET(2)] AS median_value,
    MAX(troponin_value) AS max_value
FROM `mimic-study-498508.non_traumatic_sah_study.troponin_0_48h`
GROUP BY troponin_label, valueuom
ORDER BY stays_covered DESC;
```

### 1.3 聚类前总体可行性

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.pre_clustering_feasibility_summary`
ORDER BY eligible_primary_analysis DESC;
```

重点看主分析样本中的：

- 总样本量 `n`
- 死亡事件数 `deaths`
- 贫血人数 `anemia_n`
- 贫血死亡数 `anemia_deaths`
- 非贫血死亡数 `non_anemia_deaths`

如果死亡事件总数过少，后续多变量模型要简化。

### 1.4 最终宽表快速检查

```sql
SELECT
    COUNT(*) AS rows_all,
    COUNTIF(eligible_primary_analysis = 1) AS rows_primary,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(hospital_mortality AS FLOAT64) END) AS mortality_primary,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(early_anemia_all AS FLOAT64) END) AS anemia_primary,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(any_rbc_transfusion_48h AS FLOAT64) END) AS rbc_primary
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`;
```

## 2. 导出最终宽表

从 BigQuery 导出：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`;
```

保存为本地 CSV，例如：

```text
data/physiology_features_48h.csv
```

不要把这个 CSV 提交到 git。

## 3. 运行主聚类分析

当前 BigQuery Notebook 脚本一次性输出两套分型：

- K=3：主分析分型，写入 `phenotype_cluster_assignments`、`phenotype_outcome_summary` 等默认结果表。
- K=4：高分辨率敏感性分型，写入后缀为 `_k4_exploratory` 的结果表。
- K=3 与 K=4 的交叉关系：写入 `phenotype_k3_k4_refinement_crosstab`，用于判断 K=4 极高危小亚型是否主要来自 K=3 重症组。
- 审稿补强分析：主表现在采用 `log1p(creatinine/inr) + PCA(3PC) + K-means K=3` assignment，并写入 `phenotype_cluster_assignments`、`phenotype_outcome_summary`、`phenotype_baseline_characteristics`、`phenotype_bootstrap_stability`、`phenotype_prediction_metrics`、`phenotype_regression_models`、`phenotype_severity_score_adjusted_models` 等主结果表。原始 8 维 K-means 另写入 `phenotype_raw_kmeans_*_sensitivity`，用于敏感性参照。
- 新增审稿敏感性分析：`phenotype_log_pca_complete_case_sensitivity` 使用主 log-PCA 流程但不做中位数填补；`phenotype_24h_window_sensitivity` 使用 0-24h 同源核心变量复用主 log-PCA 流程；`phenotype_external_severity_validation` 使用 SOFA/SAPS II/OASIS/LODS 作为外部严重程度验证，而不是聚类输入。
- 病因异质性补强分析：`phenotype_strict_aneurysm_subgroup_*` 仅保留 `nsah_evidence_level >= 2` 或有动脉瘤诊断/处置证据者，重复主 log-PCA K=3 聚类，并同步输出亚组结局、外部严重程度验证和调整后死亡模型。该分析用于回应“主 non-traumatic SAH 队列是否过杂”，不替代主真实世界队列。
- Notebook 运行时同步显示可视化图表：K 选择指标图、K=3/K=4 标准化中心热图、各 phenotype 住院死亡率柱状图、phenotype x anemia 死亡率图、K=3 到 K=4 交叉热图、bootstrap 稳定性直方图、候选增强变量缺失率图和预测性能比较图。

在 BigQuery Notebook / Colab Enterprise 中运行：

```python
%run 11_bigquery_notebook_non_traumatic_sah_analysis.py
```

脚本会在主分析样本内自动对两个预设敏感性子队列重新做 K=3 聚类，并写入 `phenotype_sensitivity_cohort_summary`：

- `no_rbc_48h`：排除所有 0-48h RBC 输血患者。
- `icu_los_ge_48h`：仅保留 ICU LOS >=48h 患者。

如果需要把这些敏感性队列作为完整主流程单独重跑，可再修改脚本顶部 `COHORT_FLAG` 为 `eligible_no_transfusion_sensitivity` 或 `eligible_sensitivity_48h_los`。

## 4. 按顺序解读输出

先看默认 K=3 主分析结果表：

1. `phenotype_k_selection_metrics`
2. `phenotype_cluster_centers_zscore`
3. `phenotype_outcome_summary`
4. `phenotype_anemia_feasibility`
5. `phenotype_baseline_characteristics`
6. `phenotype_cluster_stability`
7. `phenotype_bootstrap_stability`
8. `phenotype_gcs_sensitivity_summary`
9. `phenotype_prediction_metrics`
10. `phenotype_regression_models`
11. `phenotype_severity_score_adjusted_models`
12. `phenotype_anemia_stratified_models`
13. `phenotype_candidate_feature_audit`
14. `phenotype_sensitivity_cohort_summary`
15. `phenotype_epvs_sensitivity_summary`
16. `phenotype_hb_free_sensitivity`
17. `phenotype_inr_free_sensitivity`
18. `phenotype_complete_case_sensitivity`
19. `phenotype_log_pca_kmeans_sensitivity`
20. `phenotype_log_pca_kmeans_bootstrap_stability`
21. `phenotype_log_pca_complete_case_sensitivity`
22. `phenotype_24h_window_sensitivity`
23. `phenotype_external_severity_validation`
24. `phenotype_strict_aneurysm_subgroup_summary`
25. `phenotype_strict_aneurysm_subgroup_outcomes`
26. `phenotype_strict_aneurysm_subgroup_severity_validation`
27. `phenotype_strict_aneurysm_subgroup_regression`
28. `phenotype_strict_aneurysm_subgroup_severity_score_adjusted_models`
29. `phenotype_raw_kmeans_outcome_summary_sensitivity`
30. `phenotype_raw_kmeans_bootstrap_stability_sensitivity`

再看 K=4 高分辨率敏感性结果：

1. `phenotype_cluster_centers_zscore_k4_exploratory`
2. `phenotype_outcome_summary_k4_exploratory`
3. `phenotype_anemia_feasibility_k4_exploratory`
4. `phenotype_cluster_stability_k4_exploratory`
5. `phenotype_k3_k4_refinement_crosstab`

Notebook 中对应的主文/补充图建议：

- Figure 1：cohort flowchart，来自 `cohort_flowchart_counts`。
- Figure 2：K 选择指标图 + K=3 标准化中心热图，说明为什么主分型选 K=3。
- Figure 3：K=3 各 phenotype 住院死亡率和 phenotype x anemia 死亡率，展示风险分层和贫血信号。
- Supplementary Figure：K=3 到 K=4 交叉热图，说明 K=4 极高危小亚型是 K=3 重症组内的高分辨率切分，而不是主分型替代方案。
- Supplementary Figure：bootstrap ARI/min cluster size 和 GCS 敏感性结果，回应审稿人对聚类稳定性和神经功能变量选择的质疑。
- Supplementary Figure：候选变量缺失率图，支持乳酸、PaO2/FiO2、troponin 不进入主聚类的理由。
- Supplementary Figure：死亡预测 AUROC/Brier 图，说明 phenotype 的风险分层价值不只等同于单个 GCS 指标。
- Supplementary Table：`phenotype_anemia_stratified_models`，用于报告各 phenotype 内贫血 aOR；稀疏格子只报告事件数，不做强解释。
- Supplementary Table：`phenotype_sensitivity_cohort_summary`、`phenotype_epvs_sensitivity_summary`、`phenotype_hb_free_sensitivity`、`phenotype_log_pca_kmeans_sensitivity`、`phenotype_log_pca_complete_case_sensitivity`、`phenotype_24h_window_sensitivity`、`phenotype_strict_aneurysm_subgroup_*`、`phenotype_external_severity_validation`、`phenotype_severity_score_adjusted_models` 和 `phenotype_log_pca_kmeans_bootstrap_stability`，用于回应输血、ICU 停留时间、病因异质性、ePVS、Hb 循环论证、右偏极端值、PCA 几何空间、缺失值填补、时间窗选择和传统严重程度评分复核的审稿质疑。

## 5. 如何解释 K=3 和 K=4

K=3 作为主分析更合适的条件：

- 每个 cluster 样本量足够，最好每类 `N >= 100`。
- K=3 的 silhouette、最小类比例和稳定性优于 K=4。
- `phenotype_cluster_centers_zscore` 能显示清楚的生理差异。
- K=3 可解释为一个低风险表型和两个机制不同的中高危表型；P2/P3 死亡率不必严格单调，只要生理模式不同。

K=4 作为高分辨率敏感性分析的条件：

- K=4 小类具有临床合理的极重症特征，而不是异常值堆积。
- 小类死亡率显著高，但不作为复杂贫血分层回归的主要依据。
- `phenotype_k3_k4_refinement_crosstab` 显示 K=4 极高危小亚型主要来自 K=3 重症组。

推荐论文表述：

> The primary phenotype solution used log-transformed creatinine and INR, Z-score standardization, PCA, and K-means with K=3. The original standardized 8-variable K-means solution was retained as a sensitivity analysis; K=4 was evaluated as a high-resolution exploratory analysis.

## 5.1 发表前必须补齐的审稿敏感性结果

### 基线特征表

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_baseline_characteristics`
ORDER BY variable_type, variable, level, phenotype;
```

判断：

- 这张表是论文 Table 1 的主要来源，包含 Overall 和 K=3 phenotype 分层。
- 连续变量报告 median [Q1, Q3]，分类变量报告 n (%)，并给出 phenotype 间 Kruskal-Wallis 或卡方检验 p 值。
- 年龄、性别、入院类型、aneurysm evidence、贫血、输血、ICU/住院时长、GCS motor、total GCS、GCS grade 和候选严重程度评分如 SAPS II/SOFA/APS III/OASIS/LODS 都应先在这张表里审查。total GCS 和 GCS grade 可放在敏感性或补充材料中，不作为主聚类神经功能代表。若某些变量缺失率高，只能作为描述或敏感性变量，不应作为主回归强制协变量。

### GCS 敏感性

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_gcs_sensitivity_summary`
ORDER BY feature_set, phenotype;
```

判断：

- `add_total_gcs`、`gcs_total_only` 和 `gcs_grade_alternative` 相对 `primary_gcs_motor` 的 ARI 如果仍较高，说明更简洁的 GCS motor 主方案足以支撑主要表型结构。
- 如果加入或替换 GCS 指标后样本重新分配明显、死亡率模式改变，主文需明确主聚类变量选择对结果有影响，并将替代方案作为敏感性结果报告。

### Bootstrap 稳定性

查看：

```sql
SELECT
    AVG(adjusted_rand_index_vs_primary) AS mean_ari,
    APPROX_QUANTILES(adjusted_rand_index_vs_primary, 4)[OFFSET(2)] AS median_ari,
    MIN(adjusted_rand_index_vs_primary) AS min_ari,
    AVG(same_ordered_label_rate) AS mean_same_label_rate,
    MIN(min_cluster_n) AS min_cluster_n_any_bootstrap
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_bootstrap_stability`;
```

判断：

- 平均/中位 ARI 越高，K=3 assignment 越稳定。
- 如果 bootstrap ARI 偏低，仍可发表，但表述必须降级为“可复现的探索性风险分层 phenotype”，不要写成已验证临床分型。

### 预测增量

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_prediction_metrics`
ORDER BY model;
```

判断：

- 重点比较 `gcs_only`、`features_8`、`phenotype_only`、`phenotype_anemia_covariates`。
- 期望看到 phenotype 或 phenotype+协变量相对 GCS-only 有 AUROC、Brier 或校准改善。
- 如果 phenotype-only 不如 8 个原始变量，这不是失败；phenotype 的价值是压缩信息和增强可解释性。真正关键是 phenotype+贫血+协变量是否形成稳定、可解释的风险分层模型。

### 多变量回归

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_regression_models`
ORDER BY model, term;
```

判断：

- `adjusted_main_effect` 用于说明 phenotype 与死亡的关联不是单纯由年龄、性别、入院类型、aneurysm evidence level 或贫血解释。措辞应使用“associated with”，不要写成 phenotype、贫血或 INR 对死亡的因果效应。
- `adjusted_anemia_interaction` 用于探索贫血影响是否随 phenotype 改变。交互项若置信区间宽或 p 值不显著，应写成探索性信号。

### 严重程度评分调整模型

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_severity_score_adjusted_models`
ORDER BY model, term;
```

重点查看 phenotype 项：

```sql
SELECT
    model,
    term,
    odds_ratio,
    ci_lower,
    ci_upper,
    p_value,
    n,
    events
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_severity_score_adjusted_models`
WHERE term LIKE 'C(phenotype)%'
ORDER BY model, term;
```

判断：

- `phenotype_plus_sofa`、`phenotype_plus_sapsii`、`phenotype_plus_oasis`、`phenotype_plus_lods` 用于回应“你们只是重建了传统 ICU 严重程度评分”的质疑。
- `phenotype_plus_sofa_clinical` 进一步加入年龄、性别、入院类型、早期贫血和动脉瘤证据。
- 如果 P2/P3 在这些模型中仍显著，说明 phenotype 包含传统评分没有完全解释的预后信息。措辞仍应是“incremental association”或“not fully explained by severity scores”，不要写成因果效应。

### 表型内贫血调整后模型

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_anemia_stratified_models`
ORDER BY phenotype;
```

判断：

- 这张表用于报告各 K=3 phenotype 内贫血与住院死亡的调整后 OR。
- 如果 `note` 提示格子稀疏，不要解释 aOR；主文只报告贫血/非贫血事件数和死亡率。
- 若 P3 中贫血组死亡率低于非贫血组，不应解释为贫血保护作用，更可能是极重症组内残余混杂、输血/治疗选择和小样本格子共同造成。

### 预设敏感性子队列

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_sensitivity_cohort_summary`
ORDER BY analysis, phenotype;
```

判断：

- `no_rbc_48h` 用于回应“输血改变 Hb 和循环状态后是否驱动聚类”。
- `icu_los_ge_48h` 用于回应“短 ICU stay 患者测量机会不足是否驱动聚类”。
- 重点看 `ari_vs_primary_subset`、`min_cluster_n` 和各 phenotype 死亡率方向；如果方向一致，说明主分型不依赖这些选择。

### ePVS 敏感性聚类

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_epvs_sensitivity_summary`
ORDER BY feature_set, phenotype;
```

判断：

- 如果 `add_epvs_mean` 相对主 log-PCA 方案 ARI 高，说明加入 ePVS 不改变主表型，主文可把 ePVS 放在补充材料。
- 不建议把 ePVS 放入主聚类，除非能在方法中充分解释其临床含义、公式、单位转换和与 Hb 的共线性。

### 去除 Hb 后敏感性聚类

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_hb_free_sensitivity`
ORDER BY phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_hb_free_centers_zscore`
ORDER BY phenotype;
```

判断：

- 这是回应“把 Hb 放进聚类后再讨论贫血”这一循环论证质疑的关键结果。
- 重点看 `ari_vs_primary_log_pca`、各 phenotype 死亡率梯度、`early_anemia_rate` 和 `hb_min_48h_all_median`。如果去除 Hb 后仍形成相近风险梯度，说明贫血信号不是完全由 Hb 输入机械驱动。
- 如果去除 Hb 后贫血梯度和死亡率梯度明显消失，主文仍可保留 Hb 作为贫血维度，但必须把贫血结论写成“表型描述和假设生成”，不要强解释为独立预后机制。

### 去除 INR 后敏感性聚类

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_inr_free_sensitivity`
ORDER BY phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_inr_free_centers_zscore`
ORDER BY phenotype;
```

判断：

- 这是回应“INR 是否让模型几何表现变差”的变量删除敏感性分析，不是主方案替代。
- 重点看 `silhouette`、`ari_vs_primary_log_pca`、`min_cluster_n`、死亡率梯度和 `inr_max_48h_median`。如果去除 INR 后 silhouette 不升反降，说明删除 INR 没有模型性能收益。
- 如果去 INR 后 P3 仍高危但 `inr_max_48h_median` 不再清晰分层，说明凝血功能解释被削弱；主文应保留 INR，并把 no-INR 放在补充材料说明结果不是由 INR 单变量完全驱动。

### Complete-case 敏感性聚类

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_complete_case_sensitivity`
ORDER BY phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_complete_case_centers_zscore`
ORDER BY phenotype;
```

判断：

- 这是回应“中位数填补是否驱动聚类”的缺失值敏感性分析。它保留全部 8 个核心变量，只排除任一核心变量缺失的样本。
- 重点看 `excluded_missing_n`、`ari_vs_primary_subset`、`same_ordered_label_rate_vs_primary_subset`、`silhouette`、`min_cluster_n` 和死亡率梯度。
- 如果 complete-case 与主方案 ARI 高、死亡率梯度一致，说明主分型不依赖少量 INR/creatinine 缺失样本的中位数填补。

### log-PCA complete-case 敏感性聚类

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_log_pca_complete_case_sensitivity`
ORDER BY phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_log_pca_complete_case_centers_zscore`
ORDER BY phenotype;
```

判断：

- 这是比原始 complete-case 更贴近主分析的缺失值敏感性分析：同样使用 `log1p(creatinine/INR) + Z-score + PCA(3PC) + K-means K=3`，但完全不做中位数填补。
- 重点看 `excluded_missing_n`、`ari_vs_primary_log_pca_subset`、`same_ordered_label_rate_vs_primary_subset`、`silhouette_pc_space`、`min_cluster_n` 和死亡率梯度。

### 0-24h window 敏感性聚类

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_24h_window_sensitivity`
ORDER BY phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_24h_window_centers_zscore`
ORDER BY phenotype;
```

判断：

- 这是回应“0-48h 窗口是否过长”的时间窗敏感性分析。它使用同源 0-24h 核心变量，并复用主 log-PCA K-means 流程。
- 重点看 `max_feature_missing_rate`、`ari_vs_primary_log_pca`、`same_ordered_label_rate_vs_primary`、`silhouette_pc_space`、`min_cluster_n` 和死亡率梯度。
- 24h 方案若保留死亡梯度但 ARI 中等，应解释为“支持早期表型方向稳健，但 24h 与 48h 捕捉到的最差生理状态不完全相同”。

### 严格动脉瘤证据亚组

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_strict_aneurysm_subgroup_summary`
ORDER BY phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_strict_aneurysm_subgroup_outcomes`
ORDER BY phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_strict_aneurysm_subgroup_severity_validation`
ORDER BY variable, phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_strict_aneurysm_subgroup_regression`
ORDER BY model, term;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_strict_aneurysm_subgroup_severity_score_adjusted_models`
ORDER BY model, term;
```

判断：

- 严格亚组定义为 `nsah_evidence_level >= 2 OR has_aneurysm_dx = 1 OR has_aneurysm_procedure = 1`，用于提高病因特异性，不能替代主 non-traumatic SAH 真实世界队列。
- 重点看 `strict_subgroup_n`、`strict_subgroup_frac_of_primary`、`silhouette_pc_space`、`ari_vs_primary_subset`、`same_ordered_label_rate_vs_primary_subset`、最小 cluster 样本量和住院死亡率梯度。
- 如果亚组内 P1/P2/P3 仍呈清晰死亡梯度，且 SOFA/SAPS II/OASIS/LODS 验证方向一致，可在讨论中写明“findings were directionally consistent in a high-specificity aneurysm-evidence subgroup”。
- 如果亚组样本量较小或回归模型不稳定，主文只报告描述性亚组结果，把多变量模型放入补充材料并明确解释为 sensitivity rather than definitive validation。

### 外部严重程度验证

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_external_severity_validation`
ORDER BY variable, phenotype;
```

判断：

- SOFA、SAPS II、OASIS 和 LODS 只用于外部验证，不进入聚类输入。
- 重点看各评分中位数是否从 phenotype 1 到 3 递增，以及 `kruskal_p_value`、`spearman_rho_vs_ordered_phenotype` 是否支持严重程度梯度。

### log-PCA K-means 敏感性聚类

当前该方案已升级为主几何空间；本节保留为审计查询，用于核对 PCA 解释方差、载荷和 bootstrap 稳定性。

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_log_pca_kmeans_sensitivity`
ORDER BY phenotype;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_log_pca_kmeans_loadings`
ORDER BY principal_component, feature;

SELECT
    AVG(adjusted_rand_index_vs_log_pca) AS mean_ari,
    APPROX_QUANTILES(adjusted_rand_index_vs_log_pca, 4)[OFFSET(2)] AS median_ari,
    MIN(adjusted_rand_index_vs_log_pca) AS min_ari,
    AVG(same_ordered_label_rate) AS mean_same_label_rate,
    MIN(min_cluster_n) AS min_cluster_n_any_bootstrap
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_log_pca_kmeans_bootstrap_stability`;
```

判断：

- 该方案先对 `creatinine_max_48h` 和 `inr_max_48h` 做 `log1p`，再对 8 个主变量 Z-score 标准化，提取前 3 个 PC 后做 K-means K=3。
- 重点比较 `silhouette_pc_space`、`ari_vs_raw_8d_kmeans_reference`、`min_cluster_n`、死亡率梯度和前 3 个 PC 的实际解释方差。
- 若 silhouette 明显改善且死亡率梯度、临床中心方向和 raw K-means 方向一致，可在论文中作为主要几何空间方案报告；但必须透明报告 PCA 降维导致的解释方差损失。当前结果前三个 PC 解释方差约 56%，不能写成 85%。
- log-PCA bootstrap ARI 用来判断这个优化后的几何空间是否真的稳定。若 silhouette 改善但 bootstrap ARI 很低，不应把 log-PCA 方案升级为主结果。

### 原始 8 维 K-means 敏感性参照

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_raw_kmeans_outcome_summary_sensitivity`
ORDER BY phenotype;

SELECT
    AVG(adjusted_rand_index_vs_primary) AS mean_ari,
    APPROX_QUANTILES(adjusted_rand_index_vs_primary, 4)[OFFSET(2)] AS median_ari,
    MIN(adjusted_rand_index_vs_primary) AS min_ari,
    AVG(same_ordered_label_rate) AS mean_same_label_rate,
    MIN(min_cluster_n) AS min_cluster_n_any_bootstrap
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_raw_kmeans_bootstrap_stability_sensitivity`;
```

判断：

- 该方案只作为 sensitivity，不作为主分型。重点看死亡率梯度是否仍为低危、中危、高危，以及高危表型是否仍表现为 Hb/血小板低、INR/肌酐高。
- 如果 raw K-means silhouette 低于 log-PCA，但死亡率方向一致，说明 log-PCA 主要改善几何分离度，而不是人为制造新的临床结论。

### 动脉瘤诊断变量审计

查看：

```sql
SELECT
    COUNT(*) AS n,
    COUNTIF(has_aneurysm_dx = 1) AS aneurysm_dx_n,
    COUNTIF(has_aneurysm_procedure = 1) AS aneurysm_proc_n,
    COUNTIF(nsah_evidence_level = 2) AS evidence2_n,
    COUNTIF(nsah_evidence_level = 3) AS evidence3_n
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
WHERE eligible_primary_analysis = 1;

SELECT
    icd_version,
    icd_code,
    long_title
FROM `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses`
WHERE (icd_version = 9 AND REPLACE(UPPER(icd_code), '.', '') = '4373')
   OR (icd_version = 10 AND REPLACE(UPPER(icd_code), '.', '') LIKE 'I671%')
ORDER BY icd_version, icd_code;
```

判断：

- MIMIC-IV 3.1 的动脉瘤诊断字典代码为 `4373` 和 `I671`，不是带小数点的展示形式。
- 若 `has_aneurysm_dx` 再次出现全 0，优先检查是否运行了旧 SQL 或读取了旧宽表。

### ePVS/troponin 候选变量审计

查看：

```sql
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.phenotype_candidate_feature_audit`
ORDER BY missing_rate DESC;
```

判断：

- ePVS 缺失率低且分布合理时，可作为敏感性增强变量；但它和 Hb/Hct 信息高度相关，不能解释成完全独立维度。
- troponin 若缺失率高或 assay/单位混杂，建议只作为描述变量或特定心肌损伤子集分析，不进入主聚类。
- 乳酸、PaO2/FiO2、SpO2/FiO2 若仍高缺失，应继续排除在主聚类之外。

## 6. 如何判断能否解释贫血分层结果

先看 `phenotype_anemia_feasibility`，再看 `phenotype_anemia_stratified_models`。

每个 phenotype 内最好满足：

- 贫血组和非贫血组都有人。
- 每个 phenotype 内死亡事件最好 `>=20-30`。
- 贫血死亡和非贫血死亡都不要接近 0。

如果某些格子太小：

- 主分析使用总体 interaction model：
  - `mortality ~ anemia + phenotype + anemia * phenotype + covariates`
- 分 phenotype 只做描述性死亡率图。
- `phenotype_anemia_stratified_models` 中 `note` 会标记稀疏格子，论文中应主动说明这些结果仅为探索性。

## 7. 当前最重要的判断点

你现在最需要确认三件事：

1. 主分析样本量是否接近预期的 1500。
2. 8 个核心变量中有没有某个变量缺失率过高，尤其是 `spo2_min_48h`、`shock_index_max_48h` 和 `inr_max_48h`。
3. K=3 是否能形成稳定、可解释的主分型；K=4 是否只作为 K=3 重症组的高分辨率极重症切分。

这三点确认后，再进入正式结局模型和论文表图制作。
