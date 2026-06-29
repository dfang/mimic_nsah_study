# aSAH 早期多模态生理表型研究：数据提取与分析策略

## 1. 研究定位

参考文档《Early Multimodal Physiological Phenotypes and Outcomes in Aneurysmal Subarachnoid Hemorrhage》，建议将当前项目从“红细胞输血异质性治疗效应”调整为：

**基于 MIMIC-IV 3.1 的 aSAH 患者 ICU 入科后 0-48 小时多模态生理表型聚类，并分析早期贫血在不同表型中的预后意义。**

核心理由：

- aSAH 队列中红细胞输血患者数量可能很少，直接做 CATE/因果森林容易出现样本量不足、模型过拟合和不稳定估计。
- 0-48 小时内的常规 ICU 生理指标更容易完整提取，且能反映神经损伤、循环灌注、组织氧合、贫血、肾功能和凝血/炎症状态。
- 无监督聚类可以利用全 cohort，先识别“生理背景”，再分析贫血与结局的关系是否依赖表型。

## 2. 数据源与目标表位置

- 源数据库：MIMIC-IV 3.1 BigQuery
  - `physionet-data.mimiciv_3_1_hosp`
  - `physionet-data.mimiciv_3_1_icu`
- 项目中间表与最终表位置：
  - `mimic-study-498508.ash_study`

建议所有中间表使用 `CREATE OR REPLACE TABLE mimic-study-498508.ash_study.<table_name>`。

## 3. Cohort 定义

本研究建议不要只建一个 cohort，而是按“逐层递进”的方式保留筛选过程：

- `source_sah_admissions`：宽松 SAH/aSAH 候选住院，用于报告来源人群。
- `confirmed_asah_admissions`：更严格的 aSAH 住院，用于主分析候选。
- `first_icu_asah_stays`：每次住院的首次 ICU stay。
- `eligible_phenotype_cohort`：满足年龄、ICU 时长和基础数据质量要求的聚类 cohort。
- `analysis_features_48h`：最终进入 Python 聚类和结局分析的宽表。

这样做的好处是：每一步都能报告排除人数和原因，论文 flowchart 可复现，也能判断样本损失主要发生在哪个环节。

### 3.1 纳入标准

- 年龄 `>= 18` 岁。
- 诊断为 aSAH：
  - SAH ICD：ICD-9 `430`，ICD-10 `I60.x`。
  - 主分析建议使用更严格的 aSAH 定义：SAH 诊断同时合并动脉瘤诊断或动脉瘤处置证据。
  - 动脉瘤诊断可用：ICD-9 `437.3`，ICD-10 `I67.1`。
  - 如果后续能稳定提取 clipping/coiling 手术或操作代码，可作为更强确认条件。
- 有 ICU stay。
- 保留首次 ICU stay。
- ICU stay 时长 `>= 24` 小时。
- ICU 入科后 0-48 小时核心聚类变量完整度 `>= 75%`，即 8 个核心指标最多缺失 2 个。

### 3.2 排除标准

- 年龄 `< 18` 岁。
- ICU stay `< 24` 小时。
- 多次 ICU stay：仅保留首次 ICU stay，不把后续 ICU stay 当作独立样本。
- 创伤性 SAH 或非动脉瘤性 SAH，如果能通过 ICD/诊断文本识别，应排除。
- 入 ICU 后 24 小时内大量输血，建议定义为 RBC `>= 5 units` 或根据 inputevents 可用单位换算后的等价阈值。普通输血患者不要在主分析中直接排除，保留为敏感性分析。
- 核心聚类变量缺失数量 `>= 3`。

### 3.3 为什么这样定义 cohort

#### 年龄 `>=18` 岁

成人和儿童 aSAH 的病因结构、治疗策略、生命体征正常范围和预后模型不同。MIMIC-IV 中儿科样本也很少，混入儿童会增加异质性且难以调整。因此主分析限定成人患者。

#### 使用 SAH ICD + 动脉瘤证据

单独使用 ICD-9 `430` 或 ICD-10 `I60.x` 可以识别蛛网膜下腔出血，但不一定都是动脉瘤性 SAH。创伤性、自发非动脉瘤性、血管畸形相关 SAH 的病理机制和 ICU 轨迹不同。要求合并动脉瘤诊断或 clipping/coiling 证据，是为了提高 aSAH 特异性，减少错误纳入。

建议同时保留两个定义：

- 宽松定义：SAH ICD + ICU stay，用于样本量和敏感性分析。
- 严格定义：SAH ICD + 动脉瘤诊断/处置证据，用于主分析。

如果严格定义导致样本明显少于预期，需要回看 ICD/procedure 映射，而不是直接放宽标准。

#### 必须有 ICU stay

本研究的表型来自 ICU 入科后 0-48 小时的生命体征、实验室和监护数据。没有 ICU stay 就没有统一的 `icu_intime`，也无法构造可比的早期 ICU 生理窗口。

#### 只保留首次 ICU stay

同一患者或同一次住院可能有多次 ICU stay。后续 ICU stay 往往受前期治疗、并发症和转归过程影响，不能代表入院早期状态。只保留首次 ICU stay 可以避免重复样本和治疗后状态污染。

#### ICU stay `>=24h`

如果 ICU stay 很短，0-48 小时生理指标缺失会很多，而且早死/快速转出患者的测量机会不同，容易造成测量偏倚。`>=24h` 是保留样本量和保证基本监测窗口之间的折中。

同时建议报告：

- `icu_los <24h` 被排除人数。
- `24h <= icu_los <48h` 人数。
- 以 `icu_los >=48h` 作为敏感性 cohort。

#### 8 个核心变量完整度 `>=75%`

K-means 对缺失和插补敏感。如果缺失过多，聚类结果会反映“数据缺失模式”而不是生理表型。8 个核心变量最多缺失 2 个，可以在保留样本量的同时降低插补主导聚类的风险。

建议不要在 SQL 阶段过早删除缺失样本，而是在 `analysis_features_48h` 中保留 `core_feature_missing_count`，再由 Python 主分析筛选。这样可以做完整度敏感性分析。

#### 大量输血排除，普通输血保留

大量输血会直接改变 Hb、循环状态、乳酸、血小板和凝血状态，可能让 0-48 小时表型更多反映治疗干预而不是早期病情。主分析排除大量输血患者更稳妥。

普通输血患者不建议直接排除，因为：

- 样本可能不多，直接排除会降低代表性。
- 输血本身可能是严重贫血或重症状态的结果。
- 可以把 `any_rbc_transfusion_48h` 作为描述变量，并在敏感性分析中排除所有输血患者。

## 4. 时间锚点与窗口

统一使用首次 ICU 入科时间 `icu_intime` 作为 baseline。

- 聚类主窗口：`icu_intime` 到 `icu_intime + 48 hours`。
- 敏感性窗口：`icu_intime` 到 `icu_intime + 24 hours`。
- 若 ICU stay 少于 48 小时但大于 24 小时：
  - 主分析可保留并使用实际 ICU 内可观察窗口，但要在验证表中报告此类样本数量。
  - 或采用更严格规则要求 `icu_los >= 48h`，作为敏感性分析。
- 对输血影响较敏感的指标，尤其 Hb，建议提取“输血前最低值”；如果无法可靠换算输血单位，至少在敏感性分析中排除所有输血患者。

## 4.1 优化后的提取策略

### 4.1.1 先宽后严，不要一次性过滤

SQL 提取应先建立宽 cohort，再逐层标记排除条件。不要在第一张表里就把年龄、ICU 时长、缺失、输血全部过滤掉。

推荐字段：

- `is_adult`
- `has_icu_stay`
- `is_first_icu_stay`
- `icu_los_ge_24h`
- `icu_los_ge_48h`
- `strict_asah_definition`
- `massive_transfusion_24h`
- `any_rbc_transfusion_48h`
- `core_feature_missing_count`
- `eligible_primary_analysis`
- `eligible_sensitivity_48h_los`
- `eligible_no_transfusion_sensitivity`

这样最终可以一条 SQL 生成 flowchart 计数表。

### 4.1.2 aSAH 诊断建议分三档

| 层级 | 定义 | 用途 |
| --- | --- | --- |
| Level 1 | SAH ICD：`430` 或 `I60.x` | 宽松候选人群，评估样本上限 |
| Level 2 | SAH ICD + 动脉瘤诊断：`437.3` 或 `I67.1` | 主分析优先定义 |
| Level 3 | SAH ICD + clipping/coiling procedure | 高特异性敏感性分析 |

如果 Level 3 procedure code 映射质量不稳定，不要强行作为主分析标准。可先用 Level 2 做主分析，再用 Level 3 验证方向是否一致。

### 4.1.3 指标提取优先保留明细时间

每个指标明细表都应保留：

- `subject_id`
- `hadm_id`
- `stay_id`
- `charttime`
- `valuenum`
- `hours_from_icu_intime`
- `source_itemid`

原因：后续如果发现某个聚合值异常，可以回溯原始测量时间和 itemid；也方便重跑 24h、48h、输血前等不同窗口。

### 4.1.4 0-48h 聚合规则要按变量生理意义决定

不要所有变量都取平均值。主聚类应使用能代表“最差早期状态”的指标：

- Hb：最低值。
- GCS motor：最低值，但需在结果解释中强调镇静影响。
- MAP：最低值。
- Shock index：最大值。
- Lactate：最大值。
- SpO2/FiO2：最低值。
- Creatinine：最大值。
- Platelet：最低值。

可同时保留 `mean`, `first`, `last`, `measurement_count`，但主聚类只用预先定义的 8 个极值，避免分析者自由度过大。

### 4.1.5 FiO2 与氧合变量单独做质量控制

FiO2 是最容易出错的变量。建议先建 `fio2_cleaned_0_48h`：

- 如果 `valuenum BETWEEN 0.21 AND 1.0`，按比例保留。
- 如果 `valuenum BETWEEN 21 AND 100`，转换为 `valuenum / 100`。
- 其他值设为 NULL。

SpO2/FiO2 匹配建议用最近邻匹配，而不是强制同一 charttime：

- 对每条 SpO2，找前后 2 小时内最近 FiO2。
- 若同一 SpO2 有多个 FiO2，取时间差最小者。
- 聚合为 `MIN(spo2 / fio2_clean)`。

### 4.1.6 Shock index 不应只依赖同一分钟记录

HR 和 SBP 在 chartevents 中不一定同一 `charttime`。建议：

- 首选同一 charttime 匹配。
- 如果覆盖率不足，改用 HR 前后 30 分钟内最近 SBP。
- 验证同一时刻匹配和近邻匹配的覆盖率差异。

### 4.1.7 Hb 与输血时间关系要显式标记

主表建议同时保留：

- `hb_min_48h_all`
- `hb_min_48h_pre_transfusion`
- `first_rbc_time_48h`
- `any_rbc_transfusion_before_hb_min`
- `early_anemia_all`
- `early_anemia_pre_transfusion`

主分析可以使用 `hb_min_48h_all`，但敏感性分析应使用 `hb_min_48h_pre_transfusion` 或排除输血患者，避免“输血后 Hb 被治疗改变”影响贫血分类。

### 4.1.8 建议增加 feasibility table

在聚类之后、正式回归之前，必须生成：

| phenotype | N | deaths | anemia N | non-anemia N | anemia deaths | non-anemia deaths |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |

如果某个 phenotype 内死亡事件太少，不要做复杂分层多变量回归。优先使用总体 interaction model，分层结果作为描述性或惩罚回归敏感性结果。

## 5. 核心聚类变量

建议采用 8 个常规可提取指标，对应文档中的 6 个生理维度。

| 维度 | 变量名 | 提取规则 | MIMIC-IV 3.1 参考来源 |
| --- | --- | --- | --- |
| 贫血 | `hb_min_48h` | 0-48h 最低 Hb，优先输血前 | `hosp.labevents`, itemid `51222` |
| 神经功能 | `gcs_motor_min_48h` | 0-48h 最低 GCS motor | `icu.chartevents`, itemid `220739` |
| 循环灌注 | `map_min_48h` | 0-48h 最低 MAP | `icu.chartevents`, itemid `220181`, 可核对 `225309` |
| 循环灌注 | `shock_index_max_48h` | 0-48h 最大 HR/SBP | HR `220045`, SBP `220179` |
| 组织灌注 | `lactate_max_48h` | 0-48h 最高乳酸 | `hosp.labevents`, itemid `50813` |
| 氧合 | `spo2_fio2_min_48h` | 0-48h 最低 SpO2/FiO2 | SpO2 `220277`, FiO2 `223835` |
| 肾功能 | `creatinine_max_48h` | 0-48h 最高肌酐 | `hosp.labevents`, itemid `50912` |
| 凝血/炎症 | `platelet_min_48h` | 0-48h 最低血小板 | `hosp.labevents`, itemid `51265` |

可选增强变量：

- `pf_ratio_min_48h`：PaO2/FiO2，PaO2 `50821`，FiO2 `223835`。可作为 SpO2/FiO2 的替代或敏感性分析变量。
- `sofa_24h` 或简化 SOFA：用于预测性能比较，不建议纳入主聚类，避免和核心生理变量重复。

## 6. 合理范围过滤

建议在 SQL 层进行初步过滤，并在 Python 层再次审查分布。

| 变量 | 建议范围 |
| --- | --- |
| Hb | `3-25 g/dL` |
| GCS motor | `1-6` |
| MAP | `30-200 mmHg` |
| HR | `30-220 bpm` |
| SBP | `50-260 mmHg` |
| Shock index | `0.1-5`，聚合后再审查极端值 |
| Lactate | `0-30 mmol/L` |
| SpO2 | `50-100%` |
| FiO2 | 统一为比例 `0.21-1.0`；若原值为 `21-100`，转换为 `/100` |
| Creatinine | `0.1-20 mg/dL` |
| Platelet | `10-1000 K/uL` |

## 7. 推荐 BigQuery 中间表

### 7.1 Cohort 表

- `sah_patients`
  - aSAH 候选住院。
  - 字段：`subject_id`, `hadm_id`, `admittime`, `dischtime`, `hospital_expire_flag`, `race`, `admission_type`, `insurance`。

- `first_icu_stay`
  - 每次 aSAH 住院的首次 ICU stay。
  - 字段：`subject_id`, `hadm_id`, `stay_id`, `icu_intime`, `icu_outtime`, `icu_los_hours`。

- `eligible_icu_cohort`
  - 纳入年龄、ICU 时长等基础条件后的 cohort。
  - 字段：人口学、ICU 时间、死亡结局、住院/ICU LOS。

### 7.2 原始窗口指标表

建议每类指标先建明细表，再建聚合表：

- `hb_0_48h`
- `gcs_motor_0_48h`
- `map_0_48h`
- `heart_rate_0_48h`
- `sbp_0_48h`
- `shock_index_0_48h`
- `lactate_0_48h`
- `spo2_0_48h`
- `fio2_0_48h`
- `spo2_fio2_0_48h`
- `creatinine_0_48h`
- `platelet_0_48h`
- `rbc_transfusion_0_24h`
- `rbc_transfusion_0_48h`

### 7.3 聚类宽表

- `physiology_features_48h`
  - 一行一个 `stay_id`。
  - 包含 8 个核心聚类变量、早期贫血状态、缺失计数和基础结局。

建议字段：

- IDs：`subject_id`, `hadm_id`, `stay_id`
- 人口学：`age`, `gender`, `race`, `admission_type`
- 时间：`icu_intime`, `icu_outtime`, `icu_los_hours`, `hospital_los_days`
- 结局：`hospital_mortality`, `icu_mortality`, `icu_los_days`, `discharge_location`
- 聚类变量：
  - `hb_min_48h`
  - `gcs_motor_min_48h`
  - `map_min_48h`
  - `shock_index_max_48h`
  - `lactate_max_48h`
  - `spo2_fio2_min_48h`
  - `creatinine_max_48h`
  - `platelet_min_48h`
- 派生变量：
  - `early_anemia`: `hb_min_48h < 10`
  - `core_feature_missing_count`
  - `massive_transfusion_24h`
  - `any_rbc_transfusion_48h`

## 8. 每步数据验证要求

每张中间表后都应加验证 SQL。

### Cohort 验证

- 总行数、患者数、住院数、stay 数。
- `subject_id + hadm_id + stay_id` 是否唯一。
- ICU stay 时长分布，`<24h`, `<48h` 数量。
- 年龄范围，`<18` 数量。
- 住院死亡率和 ICU 死亡率。

### 指标验证

- 每个变量的测量条数、覆盖 stay 数、缺失 stay 数。
- 最小值、中位数、最大值。
- 是否存在窗口外记录。
- FiO2 是否存在 `21-100` 百分数单位，需要转换。
- Shock index 同时刻 HR/SBP 匹配数量；若过少，改用最近邻匹配。

### 宽表验证

- 8 个核心变量非缺失率。
- `core_feature_missing_count` 分布。
- 最终纳入样本数。
- 早期贫血比例。
- 输血患者比例和大量输血患者数量。

## 9. Python 分析流程

### 9.1 数据预处理

输入：`physiology_features_48h` 导出的 DataFrame。

步骤：

1. 仅保留 `core_feature_missing_count <= 2` 的样本。
2. 排除 `massive_transfusion_24h = 1`。
3. 连续变量缺失率：
   - `<20%`：中位数填补。
   - `>=20%`：变量或样本需单独评估，主分析避免过度插补。
4. 对 8 个聚类变量做 Z-score 标准化。
5. 固定随机种子 `42`。

### 9.2 无监督聚类

主分析：

- 算法：K-means。
- K 候选：`2, 3, 4`，必要时扩展到 `5` 作为探索。
- 选择依据：
  - elbow plot。
  - silhouette score。
  - Calinski-Harabasz score。
  - Davies-Bouldin score。
  - 临床可解释性。

建议默认目标：`K=4`，但必须由指标和临床解释共同支持。

稳定性验证：

- Bootstrap 重采样后计算 cluster assignment 稳定性。
- 替代算法：hierarchical clustering。
- 对 24h 窗口重复聚类。
- 排除所有输血患者后重复聚类。

### 9.3 表型命名

根据各 cluster 的标准化中心和原始变量分布命名，不要提前硬编码。

可参考命名：

- 轻度生理紊乱型。
- 孤立神经重症型。
- 循环衰竭型。
- 混合多器官重症型。

命名规则：

- 使用 cluster center 的方向解释：例如低 GCS motor、低 MAP、高 lactate、高 shock index、低 Hb、高 creatinine、低 platelet。
- 输出 radar plot、heatmap 和每组原始中位数表。

### 9.4 结局分析

主要结局：

- `hospital_mortality`。

次要结局：

- `icu_mortality`。
- `icu_los_days`。
- `hospital_los_days`。
- `discharge_location`。
- 机械通气时长和 AKI 可作为第二阶段增强结局，前提是提取质量可靠。

统计模型：

- 表型与住院死亡：
  - Logistic regression。
  - 参考组：死亡率最低或“轻度生理紊乱型”。
  - 调整变量：年龄、性别、种族、入院类型，必要时加保险、合并症或简化 SOFA。

- ICU/hospital LOS：
  - 分布偏态时用 Kruskal-Wallis。
  - 回归可用 negative binomial 或 log-transformed linear model。

- 生存时间：
  - 如果能构建住院内 time-to-death，可画 Kaplan-Meier 曲线并做 log-rank test。

### 9.5 贫血的表型依赖效应

早期贫血定义：

- 主定义：`early_anemia = hb_min_48h < 10 g/dL`。

核心分析：

1. 总体模型：
   - `hospital_mortality ~ early_anemia + phenotype + early_anemia * phenotype + covariates`
   - 重点报告 interaction P 值。

2. 分表型模型：
   - 在每个 phenotype 内分别建 logistic regression：
   - `hospital_mortality ~ early_anemia + age + gender + race + admission_type`
   - 报告各 phenotype 内 anemia 的 aOR 和 95% CI。

3. 可视化：
   - 各 phenotype 内贫血 vs 非贫血死亡率柱状图。
   - Forest plot：不同 phenotype 中 anemia 的 aOR。

敏感性贫血阈值：

- `Hb < 7 g/dL`
- `Hb < 12 g/dL`
- 使用 24h Hb 最低值替代 48h。

## 10. 可解释性分析

### 10.1 聚类解释

K-means 本身可解释性较强，应先报告：

- 标准化 cluster center heatmap。
- 各 cluster 的 8 个变量原始中位数和 IQR。
- Radar plot。

### 10.2 SHAP

SHAP 不直接解释 K-means，但可用两个代理任务：

1. 表型分类解释：
   - 用 XGBoost/RandomForest 预测 `phenotype`。
   - 输入 8 个聚类变量。
   - 用 SHAP 解释哪些变量驱动表型分配。

2. 死亡预测解释：
   - 用 XGBoost/Logistic 模型预测 `hospital_mortality`。
   - 输入 `phenotype + early_anemia + covariates`。
   - 用 SHAP 判断 phenotype 和 anemia 的贡献。

## 11. 预测性能比较

比较以下模型对住院死亡的预测能力：

- Model A：单独 Hb 或 `early_anemia`。
- Model B：GCS motor 或可得的 GCS/SOFA。
- Model C：8 个生理指标。
- Model D：phenotype。
- Model E：phenotype + early_anemia + covariates。

指标：

- AUROC。
- AUPRC，尤其当死亡率较低时。
- Calibration curve。
- Brier score。
- Decision curve analysis 可作为增强项。

## 12. 敏感性分析

必须做：

- 24h 窗口替代 48h 窗口。
- 排除所有 RBC 输血患者。
- 排除 24h 内大量输血患者。
- Hb 阈值改为 `<7` 和 `<12`。
- K-means 改为 hierarchical clustering。
- 使用 PaO2/FiO2 替代 SpO2/FiO2，限有 ABG 的子集。

建议做：

- 要求 ICU LOS `>=48h` 的严格 cohort。
- 对缺失值做 complete-case 分析，与中位数填补结果对照。
- 对 MIMIC-IV 3.1 的 itemid 候选进行一次字典审查，避免跨版本 itemid 差异。

## 13. 推荐产出文件

建议后续将当前 notebook 或脚本重构为：

- `01_create_phenotype_cohort.sql`
  - cohort、0-48h 明细指标、聚合宽表、验证 SQL。
- `02_export_features.py`
  - 从 BigQuery 导出 `physiology_features_48h`。
- `03_cluster_phenotypes.py`
  - 缺失处理、标准化、K 选择、聚类、表型命名图。
- `04_outcome_analysis.py`
  - 表型结局比较、贫血交互、分层回归。
- `05_sensitivity_analysis.py`
  - 24h、排除输血、不同 Hb 阈值、替代聚类算法。
- `06_figures_tables.py`
  - 论文表 1、表型中心热图、雷达图、forest plot、AUROC/calibration。

## 14. 与当前项目的关系

当前 `deepseek_bigquery_notebook.ipynb` 已经包含 aSAH cohort、Hb、输血、MAP、乳酸、PF ratio、GCS、心率、休克指数、血小板等提取逻辑。若按本文档转向表型聚类，需要做以下调整：

- 时间锚点从“首次贫血 T0 前”改为“首次 ICU 入科后 0-48h”。
- 暴露从“输血分组”改为“早期贫血状态 + 生理 phenotype”。
- 主建模从 causal forest/CATE 改为 K-means 聚类 + logistic interaction model。
- 保留输血变量，但作为排除/敏感性分析因素，而不是核心暴露。
- 增加肌酐、SpO2/FiO2、ICU mortality、LOS、discharge location 等变量。

## 15. 首选实施顺序

1. 在 BigQuery 中生成 `eligible_icu_cohort`。
2. 提取 0-48h 八个核心指标，并逐项验证覆盖率。
3. 生成 `physiology_features_48h`，检查缺失计数和最终样本量。
4. Python 中完成标准化、K 选择和主聚类。
5. 输出 phenotype 特征图，先做临床命名。
6. 做 phenotype 与死亡/LOS 的关联分析。
7. 做 `early_anemia * phenotype` 交互分析。
8. 做敏感性分析和预测性能比较。
