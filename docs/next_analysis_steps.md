# SQL 执行后下一步分析流程

SQL 已生成 cohort 中间表后，下一步不要马上写结论。先按以下顺序检查数据质量、导出宽表、运行聚类，再决定是否采用 4 类表型和是否能做贫血分层回归。

## 1. 先在 BigQuery 检查关键结果表

### 1.0 Derived schema 与来源贡献

运行 `10_create_non_traumatic_sah_cohort.sql` 时，脚本开头会先列出 `mimiciv_3_1_derived` 中关键表的可用字段。重点确认这些字段存在：

- `complete_blood_count`: `hemoglobin`, `platelet`
- `complete_blood_count`: `hematocrit`，用于 ePVS 候选变量
- `chemistry`: `creatinine`
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

当前主聚类使用 8 个低缺失变量：`hb_min_48h_all`、`gcs_min_48h`、`gcs_grade_min_48h`、`map_min_48h`、`shock_index_max_48h`、`spo2_min_48h`、`creatinine_max_48h`、`platelet_min_48h`。`lactate_max_48h`、`pao2_fio2_min_48h`、`spo2_fio2_min_48h` 和 `oxygenation_min_48h` 是敏感性字段，不进入主聚类。

同时检查候选增强变量：

- `epvs_mean_48h_candidate`：若缺失率低、分布合理，可考虑敏感性聚类；不要和 Hb 主变量的重复信息解释为独立生理维度。
- `troponin_peak_48h_candidate`：先看缺失率、assay label 和单位。若只在少数疑似心肌损伤患者中检测，建议作为描述/分层变量，不进入主聚类。

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

在 BigQuery Notebook / Colab Enterprise 中运行：

```python
%run 11_bigquery_notebook_non_traumatic_sah_analysis.py
```

如需做不同 cohort 的敏感性分析，修改脚本顶部 `COHORT_FLAG` 后重跑：

- `eligible_no_transfusion_sensitivity`
- `eligible_sensitivity_48h_los`

## 4. 按顺序解读输出

先看默认 K=3 主分析结果表：

1. `phenotype_k_selection_metrics`
2. `phenotype_cluster_centers_zscore`
3. `phenotype_outcome_summary`
4. `phenotype_anemia_feasibility`
5. `phenotype_cluster_stability`

再看 K=4 高分辨率敏感性结果：

1. `phenotype_cluster_centers_zscore_k4_exploratory`
2. `phenotype_outcome_summary_k4_exploratory`
3. `phenotype_anemia_feasibility_k4_exploratory`
4. `phenotype_cluster_stability_k4_exploratory`
5. `phenotype_k3_k4_refinement_crosstab`

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

> K=3 was used as the primary phenotype solution for stability and interpretability. K=4 was evaluated as a high-resolution sensitivity analysis and identified a small extreme high-risk subgroup within the severe phenotype.

## 6. 如何判断能否做贫血分层回归

看 `phenotype_anemia_feasibility.csv`。

每个 phenotype 内最好满足：

- 贫血组和非贫血组都有人。
- 每个 phenotype 内死亡事件最好 `>=20-30`。
- 贫血死亡和非贫血死亡都不要接近 0。

如果某些格子太小：

- 主分析使用总体 interaction model：
  - `mortality ~ anemia + phenotype + anemia * phenotype + covariates`
- 分 phenotype 只做描述性死亡率图。
- 后续需要 `statsmodels` 或 R 才能正式输出 OR、95% CI 和交互 P 值。

## 7. 当前最重要的判断点

你现在最需要确认三件事：

1. 主分析样本量是否接近预期的 1500。
2. 8 个核心变量中有没有某个变量缺失率过高，尤其是 `spo2_min_48h` 和 `shock_index_max_48h`。
3. K=3 是否能形成稳定、可解释的主分型；K=4 是否只作为 K=3 重症组的高分辨率极重症切分。

这三点确认后，再进入正式结局模型和论文表图制作。
