# non-traumatic SAH 研究范围切换说明

## 1. 数据集命名

- 既往 aSAH 研究中间结果保留到：`mimic-study-498508.asah_study`
- 当前 non-traumatic SAH 主研究写入：`mimic-study-498508.non_traumatic_sah_study`
- 如果 BigQuery 中仍只有旧的 `ash_study`，先运行 `00_migrate_ash_study_to_asah_study.sql`，把旧表复制到 `asah_study`。
- 当前特征提取使用 MIMIC-IV 3.1 BigQuery 三个源数据集：
  - `physionet-data.mimiciv_3_1_hosp`
  - `physionet-data.mimiciv_3_1_icu`
  - `physionet-data.mimiciv_3_1_derived`

BigQuery 不支持直接 rename dataset。迁移脚本只复制表，不删除旧 `ash_study`。

## 2. 当前主 cohort 定义

当前主研究不再要求 aSAH 证据，定义为：

- 成人患者：`anchor_age >= 18`
- 有 SAH ICD 诊断：ICD-9 `430%` 或 ICD-10 `I60%`
- 排除明确创伤性 SAH：
  - ICD-10 `S06.6%`
  - 或诊断标题提示 traumatic subarachnoid hemorrhage
  - 但必须避免把 `nontraumatic subarachnoid hemorrhage` 误判为 traumatic
- 同一患者只保留首次 non-traumatic SAH 住院
- 需要 ICU stay，主分析要求 ICU LOS >=24h

动脉瘤诊断和动脉瘤处置证据不作为主 cohort 纳入条件，而是保留为分层和敏感性分析变量。

## 3. 推荐运行顺序

1. 如需保留旧 aSAH 结果：
   ```sql
   -- BigQuery 中运行
   00_migrate_ash_study_to_asah_study.sql
   ```

2. 生成新的 non-traumatic SAH cohort：
   ```sql
   -- BigQuery 中运行
   10_create_non_traumatic_sah_cohort.sql
   ```

3. 在 BigQuery Notebook 中运行聚类分析：
   ```python
   %run 11_bigquery_notebook_non_traumatic_sah_analysis.py
   ```

4. 首先查看：
   ```sql
   SELECT *
   FROM `mimic-study-498508.non_traumatic_sah_study.cohort_flowchart_counts`
   ORDER BY step;

   SELECT *
   FROM `mimic-study-498508.non_traumatic_sah_study.feature_missingness_summary`
   ORDER BY missing_rate DESC;
   ```

## 4. 衍生表优先的指标提取策略

`mimiciv_3_1_derived` 是基于 `hosp` 和 `icu` 原始表二次加工的社区衍生数据集。当前 non-traumatic SAH 主脚本采用 derived 优先，以减少手工 itemid 映射遗漏和指标缺失：

- Hb、platelet：`complete_blood_count`
- Hct/ePVS：`complete_blood_count`，作为候选增强变量，不默认进入主聚类
- Creatinine：`chemistry`
- Total GCS / GCS grade：`gcs`
- GCS motor 敏感性变量：`gcsmotor`
- MAP、HR、SBP、SpO2：`vitalsign`
- Lactate、PaO2、PaO2/FiO2：`bg`，仅作为描述/敏感性变量；主聚类不依赖血气或 FiO2
- Troponin：`hosp.labevents` + `hosp.d_labitems` 动态识别，作为心肌损伤候选增强变量；需先审计 assay 和单位

原始 `hosp.labevents`、`icu.chartevents` 仍用于 cohort/输血等必须来自原始表的部分，以及 derived 不覆盖时的兜底或审计。脚本保留 `source_table` 字段，便于比较 derived 与原始来源的覆盖率贡献。

## 5. 主要敏感性分析

- 限定 `nsah_evidence_level >= 2`，近似回到更特异的 aSAH-like 人群。
- 限定 ICU LOS >=48h。
- 排除 0-48h 内任何 RBC 输血患者，检查 Hb 和循环表型是否受治疗影响。

这些敏感性分析用于回应审稿人关于病因异质性、非动脉瘤性 SAH 混入、治疗后特征污染和样本选择偏倚的质疑。
