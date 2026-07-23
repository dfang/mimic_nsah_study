# Statistical Analysis Plan

## MIMIC-NSAH-PHENO-01

```yaml
study_id: "MIMIC-NSAH-PHENO-01"
sap_version: "1.0.1"
protocol_version: "1.0.0"
status: FROZEN_EXPLORATORY
freeze_decision: FROZEN_2026-07-16
amendment_status: "POST_FREEZE_DOCUMENTATION_CORRECTION_2026-07-23"
analysis_results_changed: false
design_family: "phenotyping"
confirmatory_status: "exploratory"
outcome_access_before_freeze: "accessed"
analysis_unit: "ICU stay"
key_columns: ["subject_id", "hadm_id", "stay_id"]
primary_algorithm: "log1p(creatinine, INR) + median imputation + z-score + PCA(3 PCs) + K-means(K=3)"
primary_external_criterion: "in-hospital mortality as a descriptive same-hospital criterion; no landmark follow-up start"
confidence_level: 0.95
software:
  language: "Python and GoogleSQL"
  package_versions_lock: "reproducibility/requirements-bigquery.lock"
  random_seed_policy: "base seed 42; deterministic derived seeds for resampling"
```

## 1. 分析定位

本 SAP 规范当前 MIMIC-IV 开发表型分析。由于研究结果在本文件形成前已经被访问，所有分析均按探索性处理。K=3、PCA 3 个成分、部分敏感性分析和回归模型不得描述为揭盲前预设。未来确认性验证应使用独立数据和单独冻结的方案。

本 SAP 优先约束未来重跑和论文解释；当它与当前代码不一致时，不静默追认代码行为，而在“实现差异与冻结阻塞项”中明确列出。

## 2. 分析人群与粒度

### 2.1 Cohort sets

| 分析集 | 草案定义 | 用途 |
|---|---|---|
| 宽表队列 | 成人 non-traumatic SAH、每次住院首次 ICU stay、ICU LOS ≥24h | flow 与缺失审计 |
| 当前 phenotype discovery set | 宽表队列 + 八变量缺失≤2 + 排除 0–24h 大量 RBC | 当前代码的主聚类 |
| include-all transfusion sensitivity | 宽表队列 + 八变量缺失≤2，不排除 0–24h 大量 RBC | 评估 post-entry 选择影响 |
| 48h LOS sensitivity | discovery 条件 + ICU LOS ≥48h | 完整观察机会敏感性 |
| no-RBC sensitivity | discovery 条件 + 0–48h 无记录 RBC | 治疗污染敏感性 |
| complete-case sensitivity | 八项核心变量均完整 | 插补依赖敏感性 |
| strict aneurysm-evidence sensitivity | 破裂动脉瘤性 SAH 诊断或动脉瘤处置证据 | 病因特异性敏感性 |

当前每次住院可贡献一个 stay，同一患者可能重复。冻结规则保留重复住院，所有 bootstrap、训练/验证划分和稳健性评估以 `subject_id` 为最高依赖单位。

### 2.2 Flow counts

在不输出患者级值的前提下记录每一步的 stays、admissions 和 distinct subjects：

1. 所有 SAH 诊断住院；
2. 成人；
3. 排除明确创伤性 SAH；
4. 有 ICU stay；
5. 每次住院首次 ICU stay；
6. ICU LOS ≥24h；
7. 八项核心变量缺失≤2；
8. 当前主分析排除大量输血；
9. 各敏感性人群。

## 3. 变量和时间

### 3.1 主聚类变量

| Feature | Summary | Transform | Direction used only for phenotype ordering |
|---|---|---|---:|
| `hb_min_48h_all` | minimum in [0,48h) | none | −1 |
| `gcs_motor_min_48h` | minimum in [0,48h) | none | −1 |
| `map_min_48h` | minimum in [0,48h) | none | −1 |
| `shock_index_max_48h` | maximum in [0,48h) | none | +1 |
| `spo2_min_48h` | minimum in [0,48h) | none | −1 |
| `creatinine_max_48h` | maximum in [0,48h) | `log1p` | +1 |
| `inr_max_48h` | maximum in [0,48h) | `log1p` | +1 |
| `platelet_min_48h` | minimum in [0,48h) | none | −1 |

方向仅用于在聚类后把 raw labels 排成 P1、P2、P3，不参与 K-means 距离。严禁用死亡率为 cluster 重新排序或选择 K。

### 3.2 主要结局

`hospital_mortality = hospital_expire_flag`。本版冻结为全住院描述性关联，不定义 landmark follow-up start。死亡可能发生在 0–48h 特征窗口内，因此结果只能解释为同次住院共现，不能称为 48h 后预后、预测或因果效应。LOS ≥48h 子集用于观察机会敏感性分析。

### 3.3 次要变量

- `icu_mortality`、ICU LOS、hospital LOS：描述性。
- `early_anemia_all`: 0–48h Hb nadir <10 g/dL。
- `early_anemia_pre_transfusion`: 首次 RBC 前 Hb nadir <10 g/dL；无可用输血前 Hb 时保持缺失，不自动归为无贫血。
- 过程性治疗变量：只描述或作明确标注的探索性分析。
- SOFA/SAPS II/APS III/OASIS/LODS：外部严重程度判据，不是聚类输入。

## 4. 数据 QC

运行聚类前必须完成以下盲态 QC，不按结局分层：

1. 验证 `stay_id` 唯一性、`hadm_id`/`subject_id` 重复结构和时间顺序。
2. 报告每个核心变量的非缺失数、缺失率、测量次数和原始范围。
3. 验证临床范围过滤与单位：Hb、GCS motor、MAP、HR/SBP、SpO2、creatinine、INR、platelet。
4. 审计 INR label/unit，排除非 INR assay 混入。
5. 审计 RBC itemid、单位换算和 massive transfusion 标记。
6. 验证 HR/SBP 最近邻匹配时间差；当前 MIMIC 规则为 ±30 min。
7. 验证 `[start,end)` 边界，无 48h 后观测进入输入。
8. 单独报告 24–48h ICU stays、48h 前死亡和48h前出院的测量机会。
9. outcome、LOS、贫血标签、治疗和严重程度评分不得进入输入矩阵。

任何单位混合、时间反转、重复 key 或非预期范围必须先修复，再生成正式结果。

## 5. 缺失数据

### 5.1 分类和描述

按变量区分：

- 结构性缺失：该时段不适用或患者不在可观察环境；
- 未测量：临床团队未下单/未记录，可能反映病情和流程；
- 测量或抽取失败：有记录但单位、itemid 或链接失败。

对每项核心特征报告缺失率、按 stay 的缺失数以及测量次数。缺失模式本身不得被默认为随机。

### 5.2 当前主方法

1. 仅纳入八项核心变量最多缺失两项的 stays。
2. creatinine 和 INR 先进行 `log1p`。
3. 每列以 discovery set 中位数单次插补。
4. 插补后用 discovery set 均值和标准差做 Z-score。

该方法适用于探索性聚类的可复现主分析，但不表达缺失机制已被消除。

### 5.3 防泄漏与重采样

在任何 bootstrap、内部验证或分区分析中，插补器、scaler、PCA 和聚类模型必须在每个重采样训练集内重新拟合，再将未抽中/评估记录投影到该模型。不得在全数据上先固定 imputer/scaler/PCA 后只重采样 K-means。

同一 `subject_id` 的全部 stays 必须进入同一重采样单位或同一数据分区。

### 5.4 缺失敏感性分析

- 完整病例重复完整主流程。
- INR-free 聚类，评估选择性测 INR 的影响。
- 缺失数≤1 子集（若实现）。
- 可选多重插补仅作为结构敏感性：在每个插补数据集重跑聚类，通过共识矩阵比较；不得简单 Rubin 合并 cluster labels。

## 6. 主表型分析

### 6.1 预处理和降维

按以下固定顺序执行：

1. 选择八项核心变量；
2. 对 creatinine、INR 应用 `log1p(max(x,0))`；
3. 中位数插补；
4. Z-score 标准化；
5. PCA 提取 3 个成分；
6. 在 3-PC 空间运行 K-means。

保存并报告 imputation medians、scaler means/SDs、PCA loadings、explained variance、K-means centroids 和软件版本，以支持 frozen transport。

### 6.2 K-means 参数

```yaml
n_clusters: 3
random_state: 42
n_init: 100
input_space: "three PCA scores derived from eight transformed/scaled variables"
```

K=3 是结果访问后锁定的探索性主方案。对 K=2–5 报告 inertia、silhouette、Calinski–Harabasz、Davies–Bouldin、最小 cluster N 和比例，但不得以院内死亡梯度选择 K。

K=4 仅作为高分辨率探索性敏感性，不得替换 K=3，除非另行修订方案并明确结果知情。

### 6.3 表型排序与命名

按八项标准化中心的预定义不良方向求和，形成不使用结局的 `severity_score`，据此将 cluster 排为 P1–P3。报告 raw labels 与 ordered labels 映射。

在独立验证前使用 P1/P2/P3 或纯描述性名称。若某一表型稳定性不足或边界重叠明显，不赋予确定的临床亚型名称。

## 7. 聚类质量与稳定性

### 7.1 必报指标

- 各 phenotype 的 N 和比例；
- silhouette、Calinski–Harabasz、Davies–Bouldin；
- PCA explained variance 和 loadings；
- 200 次按 `subject_id` 的 bootstrap/subsampling；
- 每次重拟合完整 preprocessing + PCA + K-means；
- 通过最佳标签匹配计算 ARI、same-label rate；
- 每个 cluster 的 Jaccard membership stability；
- assignment margin 或到最近/次近 centroid 的距离差；
- 多随机种子重复拟合。

### 7.2 解释阈值

阈值用于降级表述，不是从数据中“证明真实 cluster”：

- 最小 phenotype 比例 <5%：标记为小型/潜在不稳定表型；
- bootstrap median ARI <0.70：不得称为稳定临床表型；
- cluster Jaccard median <0.75：该 cluster 不赋予明确临床名称；
- 多 seed 解明显不一致：报告范围并将结果降级为结构探索。

冻结代码按 `subject_id` 重采样，在每轮重拟合 imputer、scaler、PCA 和 K-means，并输出总体/OOB ARI 与 cluster-wise Jaccard。授权重跑的 200 次 bootstrap 平均 ARI 为 0.8554，中位数 0.8656，平均 OOB ARI 为 0.8578；详细证据见 `reproducibility/freeze-validation.md`。

## 8. 描述与外部判据

按 phenotype 报告连续变量 median [IQR]，分类变量 n (%)。对于聚类输入变量，组间差异是聚类构造的一部分，不作为独立假设发现。主要展示：

- 八项原始特征 profile 和标准化 heatmap；
- 年龄、性别、race group、admission type、aneurysm evidence；
- 贫血、RBC、过程性治疗和严重程度评分；
- 院内死亡及 95% CI。

极小单元格按机构披露规则抑制，不在图中显示患者级散点。

## 9. 主要关联模型

### 9.1 Frozen implemented exploratory outcome association

当前结果表中的调整后 OR 来自以下已实现模型。该公式在结局访问后锁定，仅用于复现冻结的探索性结果，不是揭盲前预设的确认性主模型：

```text
hospital_mortality ~ C(phenotype) + early_anemia_all + age + C(gender)
                     + C(admission_type_group)
                     + C(nsah_evidence_level)
                     + has_aneurysm_dx
```

若 `nsah_evidence_level` 或 `has_aneurysm_dx` 无变异则删除。冻结运行中 `has_aneurysm_procedure` 与 `nsah_evidence_level = 3` 重复，因此未进入报告模型。P1 为参考，报告 P2 vs P1、P3 vs P1 的 OR、95% CI 和未校正 P 值。该模型估计条件性、非因果性关联。

由于 `early_anemia_all` 与聚类输入中的最低 Hb 来自同一窗口，该模型存在构造性重叠和过度调整风险。表型 OR 仅作为冻结的探索性关联报告；贫血项必须结合 9.2 节的 Hb-free 敏感性分析解释。未来独立验证应在结局访问前固定不含构造性重复的主要调整集。

### 9.2 Anemia analysis

因为 Hb 同时是 phenotype 输入和贫血定义，以下分析分层解释：

1. 主表型中的 anemia rate：描述性。
2. `phenotype + anemia` 模型：探索性，明确循环调整风险。
3. Hb-free phenotype 下的 anemia model：关键敏感性分析。
4. phenotype × anemia interaction：仅在各交叉格事件充足时报告；必须报告 interaction test，不用分层显著/不显著差异推断效应修饰。

不将 anemia 分层结果解释为输血治疗指征或治疗效果异质性。

### 9.3 模型诊断和 fallback

- 报告每个模型 N、events、参数自由度和收敛状态。
- 检查完全/近完全分离、极端标准误、影响点和连续年龄线性假设。
- 冻结回归使用 stay-level 模型协方差，未按 `subject_id` 聚类。主队列仅有 13 条重复患者住院记录，但 CI 仍可能略窄；该限制必须在手稿中披露。
- 年龄非线性敏感性使用限制性立方样条（结点方案冻结后实施）。
- 若稀疏或不收敛，减少非核心协变量或使用 Firth/惩罚 logistic；不得只报告成功模型。
- 不以固定“10 EPV”作为充分性证明；按 CI 宽度、事件数和参数自由度判断信息量。

## 10. 次要与探索性模型

- ICU mortality logistic：次要、探索性。
- LOS：因死亡截断，仅描述 median [IQR]；正式比较需预先指定 survivor-only 或 competing-event estimand。
- KM/Cox：活着出院是竞争事件，当前简单删失分析只作可视化/探索。若用于推断，预设 cumulative incidence 和 cause-specific hazard 或合适 competing-risk 方法。
- 预测增量：GCS-only、连续八变量、phenotype-only 等仅为探索性描述；按 `subject_id` 分组的交叉验证，在每折内拟合全部 preprocessing。不得把 phenotype 研究改写为已验证预测模型。
- 线性 logistic SHAP-style approximation：只解释死亡模型贡献，不解释 cluster assignment 或病因机制。
- 0–48h 过程性治疗固定协变量模型：因时间依赖和 immortal-time/collider 风险，仅探索性，不进入主要结论。冻结输出还同时纳入了与 `nsah_evidence_level = 3` 完全重复的动脉瘤处置指标，造成相关病因参数不可估计；该模型仅保留作审计，不作为推断结果展示。

## 11. 多重性

```yaml
hypothesis_hierarchy:
  primary:
    - "K=3 phenotype structure, size and stability（无单一假设检验）"
    - "P2/P3 versus P1 与院内死亡的探索性总体关联"
  secondary:
    - "ICU mortality and independent severity-score gradients"
    - "Hb-free anemia association"
  exploratory:
    - "phenotype × anemia interaction"
    - "pairwise phenotype comparisons"
    - "process-of-care, survival, prediction and SHAP-style analyses"
    - "K=4 and alternative algorithms/features"
control_method: "冻结结果中的逐项 P 值未统一校正。所有结果知情分析以效应量和 CI 为主，并明确标注未校正和探索性；未来确认性验证应在结局访问前固定检验族及 Holm、FDR 或其他控制方法。"
subgroups:
  prespecified:
    - "strict aneurysm evidence"
    - "no recorded RBC 0–48h"
    - "ICU LOS >=48h"
  interaction_test_required: true
```

聚类输入变量的组间 P 值不属于独立验证证据。

## 12. 样本量与信息量

数据集规模固定，使用 precision/stability assessment，不以“使用全部 MIMIC”替代论证。正式运行后在合规汇总表登记：

```yaml
total_stays: 1212
unique_admissions: 1212
unique_subjects: 1197
subjects_with_repeated_admissions: 15
primary_analysis_stays: 1186
landmark_analysis_stays: "not applicable; LOS >=48 h sensitivity N=1005"
hospital_deaths_total: 235
hospital_deaths_after_landmark: "not a frozen estimand"
phenotype_sizes: [694, 384, 108]
minimum_phenotype_fraction: 0.0911
bootstrap_effective_subjects: "subject-grouped resamples; per-iteration counts stored in authorized aggregate table"
missingness_by_feature: "reported in dist/electronic_supplementary_material.md"
```

可行性判断包括：最小 cluster 的绝对 N/比例、bootstrap 置信范围、每个死亡模型的事件数与自由度、OR CI 宽度以及 phenotype × anemia 交叉格事件数。任何事件稀疏的亚组只报告粗率和宽 CI，不作稳定调整估计。

## 13. 敏感性分析矩阵

| 风险/假设 | 预设替代 | 稳健性解释 |
|---|---|---|
| 48h 治疗污染 | 同源 0–24h 特征流程 | 表型中心和死亡关联方向大体一致；不要求标签逐例相同 |
| 观察机会不等 | ICU LOS ≥48h；48h landmark | 明确目标人群变化，报告被排除早期事件 |
| RBC 改变 Hb/循环 | 无 RBC 子集；输血前 Hb；不排除大量输血版本 | 若结构明显改变，承认治疗敏感性，不作本质化命名 |
| 单次中位数插补 | complete case；缺失≤1；可选多重插补共识 | 报告 ARI、中心漂移和 cluster size |
| INR 选择性测量 | INR-free 聚类 | 若结构不保留，INR 驱动性需成为主要限制 |
| Hb 与 anemia 循环定义 | Hb-free 聚类及 anemia 回归 | 只有 Hb-free 结果可支持相对独立的贫血关联讨论 |
| GCS 表征 | total GCS、GCS grade 替换/加入 | 报告 ARI 和结局梯度，不按结果选择版本 |
| 病因异质性 | strict aneurysm-evidence subgroup | 仅评估可迁移方向，不把亚组重新称为主队列 |
| 算法假设 | raw 8D K-means、hierarchical、GMM/LPA | 报告 ARI、entropy/BIC、cluster size；不按死亡率挑算法 |
| K 选择 | K=2–5 指标；K=4 exploratory | K=3 为结果知情锁定，其他 K 只展示结构敏感性 |
| 重复患者 | 每患者首次 admission；按 subject bootstrap | 若结果不同，优先报告患者独立方案 |
| 年龄模型形式 | age spline | 主要 phenotype contrast 方向和量级不应由线性假设决定 |
| 活着出院竞争 | cumulative incidence/cause-specific analysis | KM/Cox 仅支持性，不替代二元院内结局 |

## 14. 外部验证

当前 eICU 分析应描述为结果已访问后的探索性 external criterion/transport validation。Frozen transport 必须固定并发布以下 MIMIC 参数：

- feature definitions and clinical ranges；
- imputation medians；
- scaler mean/SD；
- PCA loadings；
- K-means centroids；
- phenotype ordering map。

eICU 不得重新拟合这些参数后仍称为 frozen transport。De novo eICU clustering 仅是结构敏感性。若需要确认性外部验证，应创建独立 `study_id`、protocol、SAP、manifest 和冻结记录，且在再次查看其结局前锁定成功标准。

## 15. 输出清单

### 15.1 主文

1. Cohort flow diagram。
2. Table 1：非输入基线特征、输入特征 profile、缺失与过程性变量。
3. K=2–5 无监督指标和 K=3 选择说明。
4. PCA loadings/explained variance。
5. K=3 phenotype heatmap 与原始 median [IQR]。
6. Cluster size、bootstrap stability、Jaccard 和 assignment margin。
7. 院内死亡粗率及主要 logistic OR/95% CI。
8. 关键敏感性矩阵。

### 15.2 Supplement

- 完整 codebook、时间窗口和临床范围。
- 缺失模式与 measurement counts。
- K=4、24h、complete-case、Hb-free、INR-free、strict aneurysm、no-RBC、LOS≥48h。
- GCS alternatives、GMM/LPA、raw K-means、hierarchical comparison。
- 预测、SHAP-style、KM/Cox 和过程性治疗探索结果。
- eICU frozen transport 参数与审计。

所有结果表必须通过小单元格和罕见组合披露审查。

## 16. 实现差异与冻结阻塞项

| SAP 要求 | 当前实现 | 冻结前动作 |
|---|---|---|
| 按患者处理重复结构 | 已按 subject_id 分组 bootstrap 和交叉验证 | 已授权重跑并登记重复患者数量 |
| 完整 pipeline bootstrap | 已在每轮重拟合 imputer/scaler/PCA/K-means | 已执行并登记总体/OOB稳定性 |
| Cluster-wise stability | 已输出 ARI、same-label、cluster Jaccard、assignment distance/margin | 保留多 seed 为后续扩展，不影响本探索性冻结 |
| 明确 outcome follow-up start | 已冻结为全住院描述性关联，follow-up start 不适用 | 保持手稿非预测、非因果措辞 |
| 48h 输入观察机会 | 主队列仅要求 LOS≥24h | 报告截短窗口；将 LOS≥48h/landmark 作为关键分析 |
| 主要回归避免构造性重复 | 冻结实现同时含 phenotype、anemia 和 `has_aneurysm_dx`；`has_aneurysm_procedure` 因与 evidence level 重复而跳过 | 已在 v1.0.1 固定实际报告公式；保持探索性定位，并将 Hb-free 分析作为贫血解释的必要敏感性分析 |
| Competing discharge | 当前 KM/Cox 将活着出院删失 | 降级为探索或实施 competing-risk 方法 |
| 多重性 | 主要对比以效应量/CI解释；探索性逐项 P 值未统一校正 | 在手稿中明确标注未校正，不用于确认性结论 |
| 样本量/事件依据 | 已登记 cohort、事件和最小表型规模 | 见冻结证据与 ESM |
| 环境和 artifact provenance | 精确依赖锁、授权 clean run、job provenance 和 hashes 已登记 | 由冻结 tag 作为不可变入口 |

## 17. Go/no-go

- [x] 主要科学问题和 design family 已定义。
- [x] 主输入空间、算法和当前 K 已记录。
- [x] 结果访问状态真实标为 `accessed`。
- [x] 治理决定覆盖真实数据处理环境。
- [x] 数据 release、access date 和关键 job provenance 已记录。
- [x] codebook 与 cohort SQL 已冻结；缺少人工图表验证作为限制保留。
- [x] 重复患者规则和 subject-level resampling 已实现。
- [x] outcome 已冻结为同次住院描述性关联，早期死亡/出院保留并限制解释。
- [x] 样本量、事件数和主要 precision 已记录。
- [x] 缺失与稳定性计划已实现；未统一多重校正的探索性结果降级解释。
- [x] 输出与代码完成自动测试、聚合对账和视觉复核。
- [x] protocol/SAP、环境、批准和 deviation log 齐全；最终 commit/tag 在冻结事务末尾创建。

结论：`FROZEN_EXPLORATORY`。分析定义、代码、聚合结果和解释边界已锁定，但不得描述为结果揭盲前方案，也不等同于 `READY_FOR_SUBMISSION`。

## 18. 版本历史

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-15 | DRAFT_BLOCKED | 根据现有实现重建 SAP；固定探索性定位并记录时间契约、患者依赖、bootstrap 和多重性缺口。 |
| 0.2.0 | 2026-07-16 | READY_FOR_AUTHORIZED_RUN | 固定同次住院描述性目标、患者分组完整流程重采样、include-all 输血敏感性和精确环境锁路径。 |
| 1.0.0 | 2026-07-16 | FROZEN_EXPLORATORY | 完成授权重跑、结果复核、聚合披露审查和冻结证据登记。 |
| 1.0.1 | 2026-07-23 | POST_FREEZE_DOCUMENTATION_CORRECTION | 按独立稿件复核纠正实际回归公式、结局访问状态、多重性和重复患者协方差说明；未重跑分析，冻结数值不变。 |
