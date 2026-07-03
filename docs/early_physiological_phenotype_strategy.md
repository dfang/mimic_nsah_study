# Non-traumatic SAH 早期多模态生理表型研究：数据提取与分析策略

## 1. 研究定位

参考文档《Early Multimodal Physiological Phenotypes and Outcomes in Non-Traumatic Subarachnoid Hemorrhage》，建议将当前项目从“红细胞输血异质性治疗效应”调整为：

**基于 MIMIC-IV 3.1 的 non-traumatic SAH 患者 ICU 入科后 0-48 小时多模态生理表型聚类，并分析早期贫血在不同表型中的预后意义。**

当前主分析的投稿定位应保持克制：这不是“发现全新临床分型并证明治疗反应差异”的因果研究，而是一个基于常规低缺失早期 ICU 指标的可解释表型研究。主结果使用 K=3，以稳定性、样本量和临床可解释性为优先；K=4 仅作为高分辨率探索，用来说明 K=3 重症表型内部存在一个真实世界中不应被忽略的极高危小亚型。

建议主文围绕三个问题展开：

1. non-traumatic SAH ICU 患者是否存在可复现、低缺失、早期即可识别的生理表型？
2. 这些表型是否对应不同死亡风险和贫血负担？
3. K=4 中的小型极高危组是否可以被解释为 K=3 重症表型内部的高分辨率尾部，而不是主分型失败？

核心理由：

- non-traumatic SAH 队列中红细胞输血患者数量可能很少，直接做 CATE/因果森林容易出现样本量不足、模型过拟合和不稳定估计。
- 0-48 小时内的常规 ICU 生理指标更容易完整提取，且能反映神经损伤、循环灌注、无创氧合、贫血、肾功能和凝血/炎症状态。
- 无监督聚类可以利用全 cohort，先识别“生理背景”，再分析贫血与结局的关系是否依赖表型。

## 2. 数据源与目标表位置

- 源数据库：MIMIC-IV 3.1 BigQuery
  - `physionet-data.mimiciv_3_1_hosp`
  - `physionet-data.mimiciv_3_1_icu`
  - `physionet-data.mimiciv_3_1_derived`
- 项目中间表与最终表位置：
  - `mimic-study-498508.non_traumatic_sah_study`

建议所有当前主研究中间表使用 `CREATE OR REPLACE TABLE mimic-study-498508.non_traumatic_sah_study.<table_name>`。既往 `asah_study` 结果应保留为历史 aSAH 分析或敏感性资料，不作为当前 non-traumatic SAH 主结果位置。

## 3. Cohort 定义

本研究建议不要只建一个 cohort，而是按“逐层递进”的方式保留筛选过程：

- `source_sah_admissions`：宽松 SAH 候选住院，用于报告来源人群。
- `non_traumatic_sah_admissions`：成人 non-traumatic SAH 住院，排除明显创伤性 SAH。
- `first_icu_nsah_stays`：每次住院的首次 ICU stay。
- `eligible_phenotype_cohort`：满足年龄、ICU 时长和基础数据质量要求的聚类 cohort。
- `analysis_features_48h`：最终进入 Python 聚类和结局分析的宽表。

这样做的好处是：每一步都能报告排除人数和原因，论文 flowchart 可复现，也能判断样本损失主要发生在哪个环节。

### 3.1 纳入标准

- 年龄 `>= 18` 岁。
- 诊断为 non-traumatic SAH：
  - SAH ICD：ICD-9 `430`，ICD-10 `I60.x`。
  - 主分析不强制要求动脉瘤诊断或 clipping/coiling 处置证据。
  - 动脉瘤诊断和动脉瘤处置证据保留为分层、协变量和敏感性分析变量。
- 有 ICU stay。
- 保留首次 ICU stay。
- ICU stay 时长 `>= 24` 小时。
- ICU 入科后 0-48 小时 7 个核心聚类变量最多缺失 2 个。

### 3.2 排除标准

- 年龄 `< 18` 岁。
- ICU stay `< 24` 小时。
- 多次 ICU stay：仅保留首次 ICU stay，不把后续 ICU stay 当作独立样本。
- 创伤性 SAH 或明确创伤相关诊断，如果能通过 ICD/诊断文本识别，应排除。
- 入 ICU 后 24 小时内大量输血，建议定义为 RBC `>= 5 units` 或根据 inputevents 可用单位换算后的等价阈值。普通输血患者不要在主分析中直接排除，保留为敏感性分析。
- 核心聚类变量缺失数量 `>= 3`。

### 3.3 为什么这样定义 cohort

#### 年龄 `>=18` 岁

成人和儿童 SAH 的病因结构、治疗策略、生命体征正常范围和预后模型不同。MIMIC-IV 中儿科样本也很少，混入儿童会增加异质性且难以调整。因此主分析限定成人患者。

#### 使用 non-traumatic SAH 主队列而非强制 aSAH 队列

单独使用 ICD-9 `430` 或 ICD-10 `I60.x` 可以识别蛛网膜下腔出血，但病因可能包括动脉瘤性、非动脉瘤性自发出血和血管畸形相关 SAH。当前研究题目和主队列定位为 non-traumatic SAH，因此主分析不强制要求动脉瘤证据；否则会把研究对象重新变成 aSAH，并明显牺牲真实世界代表性。

建议同时保留三层证据：

- Level 1：SAH ICD + 成人 + ICU stay，排除明确创伤性 SAH。
- Level 2：Level 1 + 动脉瘤诊断证据。
- Level 3：Level 1 + clipping/coiling 处置证据。

Level 2/3 不作为主分析纳入条件，而作为协变量、分层和敏感性分析。这样可以回应审稿人对病因异质性的质疑，同时不丢失 non-traumatic SAH 的真实世界范围。

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

#### 7 个核心变量最多缺失 2 个

K-means 对缺失和插补敏感。如果缺失过多，聚类结果会反映“数据缺失模式”而不是生理表型。7 个核心变量最多缺失 2 个，可以在保留样本量的同时降低插补主导聚类的风险；total GCS 不计入主聚类完整度，仅用于描述和敏感性比较。

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
- `nsah_evidence_level`
- `has_aneurysm_dx`
- `has_aneurysm_procedure`
- `massive_transfusion_24h`
- `any_rbc_transfusion_48h`
- `core_feature_missing_count`
- `eligible_primary_analysis`
- `eligible_sensitivity_48h_los`
- `eligible_no_transfusion_sensitivity`

这样最终可以一条 SQL 生成 flowchart 计数表。

### 4.1.2 non-traumatic SAH 证据建议分三档

| 层级    | 定义                                                     | 用途                                   |
| ------- | -------------------------------------------------------- | -------------------------------------- |
| Level 1 | SAH ICD：`430` 或 `I60.x`，排除明确创伤性 SAH            | 主分析候选人群，体现真实世界研究范围   |
| Level 2 | Level 1 + 动脉瘤诊断：`437.3` 或 `I67.1`                 | 协变量、分层和更高特异性敏感性分析     |
| Level 3 | Level 1 + clipping/coiling procedure                     | 高特异性敏感性分析                     |

如果 Level 3 procedure code 映射质量不稳定，不要强行作为主分析标准。Level 2/3 用于验证方向是否一致，而不是替代主队列。

### 4.1.3 指标提取优先保留明细时间

每个指标明细表都应保留：

- `subject_id`
- `hadm_id`
- `stay_id`
- `charttime`
- `valuenum`
- `hours_from_icu_intime`
- `source_itemid`
- `source_table`

原因：后续如果发现某个聚合值异常，可以回溯原始测量时间和 itemid；也方便重跑 24h、48h、输血前等不同窗口。
对 MIMIC-IV 3.1 BigQuery，早期生理指标应采用“衍生表优先、原始表兜底/审计”的策略：

- `mimiciv_3_1_derived.complete_blood_count`：Hb、platelet。
- `mimiciv_3_1_derived.chemistry`：creatinine。
- `mimiciv_3_1_derived.gcs`：total GCS、GCS motor、GCS grade。
- `mimiciv_3_1_derived.vitalsign`：MAP、HR、SBP、SpO2。
- `mimiciv_3_1_derived.bg`：lactate、PaO2、PaO2/FiO2，仅作为描述和敏感性分析来源，不进入主聚类。
- `hosp.labevents` 和 `icu.chartevents`：只在 derived 表缺少目标指标、需要额外 itemid 审计，或需要复现原始测量来源时补充。

这样做可以复用 MIMIC 社区维护的标准化清洗逻辑，减少 itemid 漏提和 FiO2/血气匹配失败带来的缺失；同时保留 `source_table` 以便报告来源贡献。

### 4.1.4 0-48h 聚合规则要按变量生理意义决定

不要所有变量都取平均值。主聚类应使用能代表“最差早期状态”的指标：

- Hb：最低值。
- GCS motor：最低 GCS motor 用作主聚类神经功能变量；total GCS 和 GCS grade 同步报告并作为替代敏感性变量。
- MAP：最低值。
- Shock index：最大值。
- Lactate：最大值，仅作为有血气/有乳酸子集的描述和敏感性变量，不进入主聚类。
- 氧合：主聚类使用最低 SpO2，避免 PaO2/FiO2 和 FiO2 匹配造成的高缺失；PaO2/FiO2、SpO2/FiO2 仅作为敏感性变量。
- Creatinine：最大值。
- Platelet：最低值。

可同时保留 `mean`, `first`, `last`, `measurement_count`，但主聚类只用预先定义的 7 个极值，避免分析者自由度过大。

### 4.1.5 氧合变量单独做质量控制

FiO2 是最容易出错的变量。单纯使用 `chartevents` 中的 SpO2 和 FiO2 会造成较高缺失，因为室内空气、鼻导管或面罩患者常常没有数值型 FiO2 记录。因此主聚类不再使用 PaO2/FiO2、SpO2/FiO2 或合成 `oxygenation_min_48h`，而使用 `spo2_min_48h` 作为低缺失无创氧合指标。

血气氧合变量仍应保留为敏感性和审计字段：

1. `pao2_fio2_0_48h`：优先使用 `mimiciv_3_1_derived.bg.pao2fio2ratio`；若需要兜底，再用血气 PaO2 与血气 FiO2 前后 2 小时最近邻匹配。
2. `spo2_fio2_0_48h`：床旁 SpO2 与 charted FiO2 前后 2 小时最近邻匹配。
3. `oxygenation_0_48h`：优先采用 PaO2/FiO2；若同一 stay 没有 PaO2/FiO2，再采用 SpO2/FiO2。

血气 FiO2 和床旁 FiO2 都应先清洗为比例：

- 如果 `valuenum BETWEEN 0.21 AND 1.0`，按比例保留。
- 如果 `valuenum BETWEEN 21 AND 100`，转换为 `valuenum / 100`。
- 其他值设为 NULL。

当需要从 PaO2/SpO2 和 FiO2 重新计算比值时，建议用最近邻匹配，而不是强制同一 `charttime`：

- 对每条 PaO2 或 SpO2，找前后 2 小时内最近 FiO2。
- 若存在多个 FiO2，取时间差最小者。
- 聚合为 `MIN(pao2fio2ratio)` 或 `MIN(pao2 / fio2_clean)`、`MIN(spo2 / fio2_clean)` 和最终 `MIN(oxygenation_ratio)`。

最终主聚类使用 `spo2_min_48h`。同时保留 `pao2_fio2_min_48h`、`spo2_fio2_min_48h`、`oxygenation_min_48h` 和 `oxygenation_source_48h`，用于报告血气/FiO2 变量覆盖率和做敏感性分析。

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

| phenotype |   N | deaths | anemia N | non-anemia N | anemia deaths | non-anemia deaths |
| --------- | --: | -----: | -------: | -----------: | ------------: | ----------------: |

如果某个 phenotype 内死亡事件太少，不要做复杂分层多变量回归。优先使用总体 interaction model，分层结果作为描述性或惩罚回归敏感性结果。

## 5. 核心聚类变量

建议采用 7 个常规可提取、低缺失指标，对应文档中的 6 个生理维度。主聚类去掉 total GCS，仅保留 GCS motor 作为神经功能输入；同时彻底剔除高缺失的乳酸、PaO2/FiO2 和合成氧合比值；不构造“终末器官低灌注复合评分”，避免引入未经验证的自创评分工具。

肌钙蛋白峰值和 ePVS 是有临床意义的候选增强变量，但不应在未审计覆盖率、单位和分布前直接进入主聚类：肌钙蛋白可能只在怀疑心肌损伤时检测，缺失具有选择性；ePVS 依赖 Hb/Hct 单位转换和性别预期值，需先确认公式实现和异常值分布。当前策略是先提取并写入宽表，作为描述/敏感性候选变量。

| 维度      | 变量名                | 提取规则                                                       | MIMIC-IV 3.1 参考来源                                                                                |
| --------- | --------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 贫血      | `hb_min_48h`          | 0-48h 最低 Hb，优先输血前                                      | 优先 `mimiciv_3_1_derived.complete_blood_count.hemoglobin`；原始审计 `hosp.labevents` itemid `51222` |
| 神经功能  | `gcs_motor_min_48h`   | 0-48h 最低 GCS motor component                                | 优先 `mimiciv_3_1_derived.gcs.gcsmotor`；编码 1-6，数值越低代表运动反应越差                             |
| 循环灌注  | `map_min_48h`         | 0-48h 最低 MAP                                                 | 优先 `mimiciv_3_1_derived.vitalsign.mbp/mbp_ni`；原始审计 itemid `220181`, `225309`                  |
| 循环灌注  | `shock_index_max_48h` | 0-48h 最大 HR/SBP                                              | 优先 `mimiciv_3_1_derived.vitalsign.heart_rate` 与 `sbp/sbp_ni`；原始审计 HR `220045`, SBP `220179`  |
| 氧合      | `spo2_min_48h`        | 0-48h 最低 SpO2                                                | 优先 `mimiciv_3_1_derived.vitalsign.spo2`；不依赖 FiO2 或血气                                        |
| 肾功能    | `creatinine_max_48h`  | 0-48h 最高肌酐                                                 | 优先 `mimiciv_3_1_derived.chemistry.creatinine`；原始审计 `hosp.labevents` itemid `50912`            |
| 凝血/炎症 | `platelet_min_48h`    | 0-48h 最低血小板                                               | 优先 `mimiciv_3_1_derived.complete_blood_count.platelet`；原始审计 `hosp.labevents` itemid `51265`   |

可选增强变量：

- `lactate_max_48h`：仅作为有乳酸记录子集的描述和敏感性分析变量，不作为主聚类变量。
- `troponin_peak_48h`：0-48h 肌钙蛋白峰值，作为神经源性心肌损伤/心源性低灌注候选变量；不同 Troponin I/T assay 单位和量纲可能不同，覆盖率和单位未验证前不进入主聚类。
- `epvs_mean_48h`、`epvs_first_48h`、`epvs_max_48h`：由 Hb/Hct 计算的估算血浆容量状态候选变量；先用于覆盖率和分布审计，若缺失率低且分布合理，可作为敏感性聚类变量。
- `pao2_fio2_min_48h`：仅使用血气 PaO2/FiO2，可作为氧合变量的血气子集敏感性分析。
- `spo2_fio2_min_48h`：仅使用床旁 SpO2/FiO2，可作为没有 PaO2/FiO2 时的补充来源。
- `oxygenation_min_48h`：PaO2/FiO2 优先、SpO2/FiO2 兜底的氧合比值，仅作为敏感性变量。
- `gcs_min_48h`：0-48h 最低 total GCS，保留为描述、Table 1、预测基线和替代敏感性变量，不作为主聚类神经变量。
- `gcs_grade_min_48h`：由最低 total GCS 派生，编码建议 1=轻度 `13-15`、2=中度 `9-12`、3=重度 `3-8`；保留为描述、分层和替代敏感性变量，不作为主聚类神经变量。
- `wfns_grade`：若有经验证的 WFNS 来源或人工标注，可作为死亡/结局模型协变量；若仅有 GCS，可报告 `wfns_gcs_grade_min_48h` 作为 GCS-only 近似，不应等同于完整 WFNS。
- `sapsiii_24h`、`sofa_24h`：用于预测性能比较和结局模型协变量，不建议纳入主聚类，避免和核心生理变量重复。若 MIMIC derived 不直接提供 SAPS III，应明确使用经验证的外部/本地评分表，或记录为不可得。

## 6. 合理范围过滤

建议在 SQL 层进行初步过滤，并在 Python 层再次审查分布。

| 变量        | 建议范围                                                                      |
| ----------- | ----------------------------------------------------------------------------- |
| Hb          | `3-25 g/dL`                                                                   |
| Total GCS   | `3-15`                                                                        |
| GCS grade   | `1-3`，其中 1=`13-15`，2=`9-12`，3=`3-8`；用于描述/替代敏感性分析              |
| GCS motor   | `1-6`                                                                         |
| MAP         | `30-200 mmHg`                                                                 |
| HR          | `30-220 bpm`                                                                  |
| SBP         | `50-260 mmHg`                                                                 |
| Shock index | `0.1-5`，聚合后再审查极端值                                                   |
| Lactate     | `0-30 mmol/L`，仅用于敏感性分析                                               |
| Troponin    | `>=0`，按 assay/单位分层审计；未标准化前不合并解释绝对量级                    |
| ePVS        | 先审查分布和极端值；Hct 统一为比例，Hb 由 g/dL 转为 g/L                       |
| SpO2        | `50-100%`                                                                     |
| FiO2        | 统一为比例 `0.21-1.0`；若原值为 `21-100`，转换为 `/100`；仅用于敏感性氧合比值 |
| Creatinine  | `0.1-20 mg/dL`                                                                |
| Platelet    | `10-1000 K/uL`                                                                |

## 7. 推荐 BigQuery 中间表

### 7.1 Cohort 表

- `sah_patients`
  - SAH 候选住院。
  - 字段：`subject_id`, `hadm_id`, `admittime`, `dischtime`, `hospital_expire_flag`, `race`, `admission_type`, `insurance`。

- `first_icu_stay`
  - 每次 non-traumatic SAH 住院的首次 ICU stay。
  - 字段：`subject_id`, `hadm_id`, `stay_id`, `icu_intime`, `icu_outtime`, `icu_los_hours`。

- `eligible_icu_cohort`
  - 纳入年龄、ICU 时长等基础条件后的 cohort。
  - 字段：人口学、ICU 时间、死亡结局、住院/ICU LOS。

### 7.2 原始窗口指标表

建议每类指标先建明细表，再建聚合表：

- `hb_0_48h`
- `gcs_0_48h`
- `map_0_48h`
- `heart_rate_0_48h`
- `sbp_0_48h`
- `shock_index_0_48h`
- `lactate_0_48h`
  - 合并官方血气衍生表 `mimiciv_3_1_derived.bg.lactate` 与原始 `hosp.labevents` itemid `50813`。
  - `bg` 优先，`labevents` 补充；同一 `stay_id + charttime + lactate` 去重，避免同一血气标本重复计数。
  - `chartevents` 仅用于审计核查，不作为主乳酸提取来源。
  - 因当前 cohort 缺失率高，乳酸不进入主聚类，仅保留为描述和敏感性字段。
- `troponin_0_48h`
  - 通过 `hosp.d_labitems` 动态识别 label 包含 troponin 的血液检验项目。
  - 保留 assay label 和单位；不同 assay 未标准化前仅作为候选增强变量。
- `epvs_0_48h`
  - 使用 `complete_blood_count` 中同一时间的 Hb 和 Hct 计算。
  - Hct 若为 `10-70` 按百分比除以 100；Hb 由 g/dL 转为 g/L。
  - 公式：`ePVS = Hb(g/L) / expected_Hb - Hct_fraction / expected_Hct`；男性 expected Hb/Hct 为 `150/0.46`，女性为 `130/0.42`。
- `spo2_0_48h`
- `blood_gas_fio2_cleaned_0_48h`
- `fio2_cleaned_0_48h`
- `pao2_0_48h`
- `pao2_fio2_0_48h`
- `spo2_fio2_0_48h`
- `oxygenation_0_48h`
- `creatinine_0_48h`
- `platelet_0_48h`
- `rbc_transfusion_0_24h`
- `rbc_transfusion_0_48h`

### 7.3 聚类宽表

- `physiology_features_48h`
  - 一行一个 `stay_id`。
  - 包含 7 个核心聚类变量、早期贫血状态、缺失计数和基础结局。

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
  - `spo2_min_48h`
  - `creatinine_max_48h`
  - `platelet_min_48h`
- 派生变量：
  - `early_anemia`: `hb_min_48h < 10`
  - `gcs_min_48h`
  - `gcs_grade_min_48h`
  - `wfns_gcs_grade_min_48h`
  - `troponin_peak_48h`
  - `troponin_labels_48h`
  - `troponin_units_48h`
  - `epvs_mean_48h`
  - `epvs_first_48h`
  - `epvs_max_48h`
  - `lactate_max_48h`
  - `pao2_fio2_min_48h`
  - `spo2_fio2_min_48h`
  - `oxygenation_min_48h`
  - `sapsiii_24h`
  - `sofa_24h`
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
- 乳酸覆盖率需分别报告 `mimiciv_3_1_derived.bg` 与 `hosp.labevents` 兜底来源贡献；若缺失率仍高，继续作为敏感性字段而非主聚类变量。
- 肌钙蛋白覆盖率需按 assay label 和单位报告；若不同 assay 混杂或缺失率高，不进入主聚类。
- ePVS 覆盖率和分布需单独报告，重点检查 Hct 单位转换、性别预期值和极端值。
- FiO2 是否存在 `21-100` 百分数单位，需要转换。
- 主氧合变量报告 `spo2_min_48h` 覆盖率；敏感性氧合变量分别报告 PaO2、血气 FiO2、PaO2/FiO2、charted FiO2、SpO2/FiO2 和 `oxygenation_min_48h`。
- Shock index 同时刻 HR/SBP 匹配数量；若过少，改用最近邻匹配。

### 宽表验证

- 7 个核心变量非缺失率。
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
4. 对 7 个聚类变量做 Z-score 标准化。
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

建议主分析默认目标：`K=3`。当前结果中 K=3 的稳定性优于 K=4，且每类样本量更适合后续贫血分层和回归。`K=4` 不作为主要分型，而作为高分辨率敏感性分析，用于观察 K=3 重症组内是否可进一步切出一个小型极高危多器官衰竭亚型。

推荐报告结构：

- 主分型：K=3，用于主要表型命名、主要结局比较、贫血交互和回归模型。
- 高分辨率敏感性分型：K=4，用于说明真实世界重症人群中存在小型极高危尾部；不在 K=4 小类内做复杂贫血分层回归。
- 交叉验证：报告 K=3 与 K=4 assignment 交叉表，确认 K=4 极高危小亚型主要来自 K=3 的重症组。

稳定性验证：

- Bootstrap 重采样后计算 cluster assignment 稳定性，输出 `phenotype_bootstrap_stability`。重点报告 bootstrap ARI 的均值、中位数、IQR 和低分位数；若稳定性不足，论文中应把表型定位为探索性、假设生成。
- 替代算法：hierarchical clustering，输出 `phenotype_cluster_stability` 中的 K-means vs hierarchical ARI。
- GCS 敏感性：主聚类当前仅包含 `gcs_motor_min_48h`。必须输出 `phenotype_gcs_sensitivity_summary`，比较 GCS motor 主方案、加入 total GCS、仅 total GCS、以及用 GCS grade 替代 motor 四套变量下 K=3 的样本量、死亡率、silhouette 和相对主方案的 ARI。若加入或替换 GCS 指标后主要表型结构仍相似，说明更简洁的 motor-only 神经输入足以支撑主表型。
- 对 24h 窗口重复聚类。
- 排除所有输血患者后重复聚类。

### 9.3 表型命名

根据各 cluster 的标准化中心和原始变量分布命名，不要提前硬编码。

可参考命名：

- 轻度生理紊乱型。
- 贫血-循环应激型。
- 神经/多器官重症型。

K=4 敏感性分析可额外命名一个小型极高危混合多器官衰竭型，但应明确这是高分辨率探索性亚型。

命名规则：

- 使用 cluster center 的方向解释：例如低 GCS motor、低 MAP、高 shock index、低 SpO2、低 Hb、高 creatinine、低 platelet；total GCS 和 GCS grade 用于描述和敏感性验证。
- 不要求 K=3 的两个中高危表型死亡率严格单调分离；若死亡率接近，但生理模式不同，可解释为机制不同、总体风险相近的中高危亚型。
- 输出 radar plot、heatmap 和每组原始中位数表。

### 9.4 结局分析

正式结局模型前应先输出 `phenotype_baseline_characteristics` 作为论文 Table 1：

- Overall 和 K=3 phenotype 分层。
- 连续变量报告 median [Q1, Q3]，同时保留 mean/SD、缺失数和非缺失数。
- 分类变量报告 n (%)，同时保留缺失数。
- phenotype 间比较使用 Kruskal-Wallis 或卡方检验，p 值只用于描述组间差异，不作为选择 phenotype 的依据。
- Table 1 至少包含年龄、性别、种族、入院类型、保险、aneurysm evidence level、动脉瘤诊断/处置证据、早期贫血、输血、ICU/住院时长、total GCS、GCS motor、GCS grade、ePVS、troponin、SAPS III/SOFA 和 7 个主聚类变量。total GCS 和 GCS grade 可作为描述或补充材料变量，不作为主聚类神经功能代表。

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
  - 最低限度调整变量：年龄、性别、入院类型、aneurysm evidence level、动脉瘤诊断/处置证据、早期贫血。
  - 扩展模型可加入种族、保险、SAPS III、SOFA 或 WFNS 近似变量，但要避免把主聚类变量全部再作为协变量纳入同一个模型，否则会过度调整并削弱 phenotype 的整体生理意义。
  - 当前脚本输出 `phenotype_regression_models`：主效应模型检验 phenotype 是否独立关联住院死亡，interaction 模型检验贫血效应是否随 phenotype 改变。交互项若样本格子较小，应按探索性结果解释。
  - 当前脚本额外输出 `phenotype_anemia_stratified_models`：在每个 K=3 phenotype 内估计早期贫血的调整后 OR。若某个 phenotype 的贫血/非贫血死亡格子太稀疏，脚本会保留 crude event counts 并把 aOR 标记为不稳定；主文不应强行解释这些稀疏 aOR。

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
- 各 cluster 的 7 个变量原始中位数和 IQR。
- K=3 各 phenotype 住院死亡率柱状图，带样本量和 95% CI。
- Phenotype x anemia 住院死亡率柱状图。
- K=3 到 K=4 refinement heatmap，用于说明极高危小亚型来自 K=3 重症表型内部。
- Bootstrap ARI 和最小 cluster size 分布图，用于支持聚类稳定性。
- 候选增强变量缺失率图，用于解释为何乳酸、PaO2/FiO2、troponin 不进入主聚类。
- 死亡预测 AUROC/Brier score 比较图，用于说明 phenotype 相对 GCS-only 的增量价值。
- Radar plot 可作为补充图，但不应替代 heatmap 和原始中位数表。

### 10.2 SHAP

SHAP 不直接解释 K-means，但可用两个代理任务：

1. 表型分类解释：
   - 用 XGBoost/RandomForest 预测 `phenotype`。
   - 输入 7 个低缺失主聚类变量。
   - 用 SHAP 解释哪些变量驱动表型分配。

2. 死亡预测解释：
   - 用 XGBoost/Logistic 模型预测 `hospital_mortality`。
   - 输入 `phenotype + early_anemia + covariates`。
   - 用 SHAP 判断 phenotype 和 anemia 的贡献。

## 11. 预测性能比较

比较以下模型对住院死亡的预测能力：

- Model A：GCS-only，作为神经功能基线模型。
- Model B：7 个主聚类生理指标。
- Model C：phenotype-only。
- Model D：phenotype + early_anemia + covariates，协变量至少包含年龄、性别、入院类型、aneurysm evidence level、动脉瘤诊断/处置证据。

指标：

- AUROC。
- Brier score。
- Calibration-in-the-large 和近似 calibration slope。
- AUPRC、calibration curve 和 decision curve analysis 可作为论文增强项。

当前脚本输出 `phenotype_prediction_metrics`。理想结果不是 phenotype-only 一定超过 7 个原始变量，而是说明 phenotype 在压缩多模态生理信息后仍能保留可解释的风险分层能力；如果 phenotype + 贫血 + 协变量相对 GCS-only 有 AUROC/Brier 改善，说明其临床风险分层价值更强。

## 12. 敏感性分析

必须做：

- 24h 窗口替代 48h 窗口。当前脚本暂未自动重建 24h 特征，需 SQL 端生成 `physiology_features_24h` 后另跑。
- 排除所有 RBC 输血患者。当前脚本输出 `phenotype_sensitivity_cohort_summary` 中的 `no_rbc_48h`，在主分析样本内重新聚类并报告 ARI、最小 cluster 和死亡率。
- ICU LOS `>=48h` 严格 cohort。当前脚本输出 `phenotype_sensitivity_cohort_summary` 中的 `icu_los_ge_48h`。
- 排除 24h 内大量输血患者。当前主 cohort 已排除 `massive_transfusion_24h = 1`，flowchart 中需报告人数。
- Hb 阈值改为 `<7` 和 `<12`。
- K-means 改为 hierarchical clustering。
- GCS 敏感性：GCS motor 主方案、加入 total GCS、total GCS only、GCS grade 替代 motor。
- 仅使用 PaO2/FiO2，限有 ABG 且可匹配 FiO2 的子集。

建议做：

- 对缺失值做 complete-case 分析，与中位数填补结果对照。
- ePVS/troponin 候选增强聚类：只有在 `phenotype_candidate_feature_audit` 显示覆盖率高、单位一致、分布合理时才作为敏感性聚类；否则仅作描述变量。当前脚本输出 `phenotype_epvs_sensitivity_summary`，比较主 8 变量、加入 `epvs_mean_48h`、用 `epvs_mean_48h` 替换 Hb 三种方案；ePVS 与 Hb/Hct 强相关，因此只能作为敏感性证据，不能作为主聚类独立维度。
- 对 MIMIC-IV 3.1 的 itemid 候选进行一次字典审查，避免跨版本 itemid 差异。

## 12.1 当前结果的投稿结论边界

基于当前运行结果，主结论可写为：

- 在 MIMIC-IV 3.1 的成年 non-traumatic SAH ICU 患者中，0-48 小时常规低缺失生理指标可识别 3 个早期表型。
- K=3 主分型比 K=4 更适合作为主文结果：K=3 样本量更均衡、稳定性更好，且能形成低风险、神经重症和混合多器官重症三个临床可解释模式。
- K=4 不应被丢弃，而应作为高分辨率探索：其小型极高危表型主要来自 K=3 重症组内部，提示真实世界中存在一个死亡率很高的极重症尾部。
- 早期贫血与表型分布和死亡风险相关，但不同 phenotype 内贫血方向和强度可能不一致；这应解释为预后异质性和混杂提示，而不是贫血的因果效应或输血获益证据。
- 乳酸、PaO2/FiO2、合成氧合比值和肌钙蛋白缺失率较高或选择性检测明显，不进入主聚类。ePVS 覆盖率较好，但与 Hb/Hct 信息重叠，因此只作为敏感性聚类。

不建议写：

- “发现了经过外部验证的临床分型。”
- “贫血导致死亡风险升高/降低。”
- “某一 phenotype 应接受输血或特定治疗。”
- “K=4 是主分型最佳解。”

## 12.2 创新性与重复风险

当前研究不能定位为“首个 MIMIC-IV SAH 机器学习研究”。已有研究使用 MIMIC-IV 做 SAH 死亡、脓毒症或并发症预测，也已有数据驱动 SAH 表型研究。可保留的创新点应更窄、更可信：

- 使用低缺失、常规可及的早期 ICU 生理变量，而不是依赖高缺失血气、乳酸或治疗后变量。
- 将 K=3 作为稳定主分型，同时把 K=4 极高危小类解释为重症组内高分辨率亚型，避免过小 cluster 造成主结果不稳定。
- 把早期贫血放在表型背景中解释，强调贫血信号可能依赖神经/循环/器官功能背景。
- 明确报告候选变量缺失率和敏感性聚类，降低审稿人对变量选择任意性的质疑。

重复风险主要来自同类 MIMIC-IV non-traumatic SAH 预测模型和少量聚类/共识分型预印本。投稿时应避免宣称“大而全的共识分型”或“治疗反应分型”，把贡献限定为早期低缺失生理表型和贫血相关预后异质性。

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
- 增加肌酐、氧合变量、ICU mortality、LOS、discharge location 等变量。

## 15. 首选实施顺序

1. 在 BigQuery 中生成 `eligible_icu_cohort`。
2. 提取 0-48h 八个核心指标，并逐项验证覆盖率。
3. 生成 `physiology_features_48h`，检查缺失计数和最终样本量。
4. Python 中完成标准化、K 选择和主聚类。
5. 输出 phenotype 特征图，先做临床命名。
6. 做 phenotype 与死亡/LOS 的关联分析。
7. 做 `early_anemia * phenotype` 交互分析。
8. 做敏感性分析和预测性能比较。
