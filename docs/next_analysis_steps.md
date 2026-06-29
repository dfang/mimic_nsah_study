# SQL 执行后下一步分析流程

SQL 已生成 cohort 中间表后，下一步不要马上写结论。先按以下顺序检查数据质量、导出宽表、运行聚类，再决定是否采用 4 类表型和是否能做贫血分层回归。

## 1. 先在 BigQuery 检查关键结果表

### 1.1 Cohort flowchart

```sql
SELECT *
FROM `mimic-study-498508.ash_study.cohort_flowchart_counts`
ORDER BY step;
```

重点看：

- `07_primary_analysis_no_massive_transfusion` 是否仍有足够样本。
- `08_sensitivity_icu_los_ge_48h` 与主分析差距是否很大。
- `09_sensitivity_no_rbc_48h` 是否保留大部分样本。

### 1.2 核心变量缺失率

```sql
SELECT *
FROM `mimic-study-498508.ash_study.feature_missingness_summary`
ORDER BY missing_rate DESC;
```

判断：

- 单个核心变量缺失率 `<20%`：中位数填补可以接受。
- 单个核心变量缺失率 `20%-40%`：主分析可谨慎保留，但必须做敏感性分析。
- 单个核心变量缺失率 `>40%`：不建议直接作为主聚类变量，考虑替换或作为敏感性分析。

### 1.3 聚类前总体可行性

```sql
SELECT *
FROM `mimic-study-498508.ash_study.pre_clustering_feasibility_summary`
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
FROM `mimic-study-498508.ash_study.physiology_features_48h`;
```

## 2. 导出最终宽表

从 BigQuery 导出：

```sql
SELECT *
FROM `mimic-study-498508.ash_study.physiology_features_48h`;
```

保存为本地 CSV，例如：

```text
data/physiology_features_48h.csv
```

不要把这个 CSV 提交到 git。

## 3. 运行主聚类分析

默认按 K=4 运行：

```bash
python3 02_analyze_phenotypes.py \
  --input data/physiology_features_48h.csv \
  --output-dir outputs/phenotype_k4 \
  --k 4
```

同时跑自动选 K：

```bash
python3 02_analyze_phenotypes.py \
  --input data/physiology_features_48h.csv \
  --output-dir outputs/phenotype_auto \
  --k auto
```

再跑两个敏感性 cohort：

```bash
python3 02_analyze_phenotypes.py \
  --input data/physiology_features_48h.csv \
  --output-dir outputs/phenotype_no_transfusion \
  --k 4 \
  --sensitivity-no-transfusion

python3 02_analyze_phenotypes.py \
  --input data/physiology_features_48h.csv \
  --output-dir outputs/phenotype_48h_los \
  --k 4 \
  --sensitivity-48h-los
```

## 4. 按顺序解读输出

每个输出目录中先看：

1. `feature_missingness.csv`
2. `k_selection_metrics.csv`
3. `k_selection_metrics.png`
4. `cluster_centers_zscore.csv`
5. `cluster_centers_heatmap.png`
6. `phenotype_outcome_summary.csv`
7. `phenotype_anemia_feasibility.csv`
8. `anemia_mortality_by_phenotype.png`
9. `cluster_stability.csv`

## 5. 如何判断 K=4 能不能用

K=4 可以作为主分析的条件：

- 每个 cluster 样本量至少占总样本 `5%`，最好每类 `N >= 100`。
- `cluster_centers_heatmap.png` 能显示清楚的生理差异。
- `phenotype_outcome_summary.csv` 中不同 phenotype 的死亡率有临床梯度或可解释差异。
- `cluster_stability.csv` 中 K-means vs hierarchical 的 adjusted Rand index 不应太低；如果很低，说明分类不稳定。
- K=4 不能产生一个只有很少样本的“垃圾类”。

如果 K=4 不稳：

- 优先比较 K=3。
- 不要强行写 4 类。
- 表型命名必须基于 cluster center，不要预设“轻度/神经/循环/混合”。

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
2. 8 个核心变量中有没有某个变量缺失率过高，尤其是 `spo2_fio2_min_48h` 和 `shock_index_max_48h`。
3. K=4 是否产生稳定且可解释的 cluster。

这三点确认后，再进入正式结局模型和论文表图制作。

