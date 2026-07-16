# Statistical Analysis Plan

## MIMIC-NSAH-PHENO-01

```yaml
study_id: "MIMIC-NSAH-PHENO-01"
sap_version: "0.1.2"
protocol_version: "0.1.2"
status: DRAFT
freeze_decision: DRAFT_BLOCKED
design_family: "phenotyping"
confirmatory_status: "exploratory"
outcome_access_before_freeze: "accessed"
analysis_unit: "ICU stay"
key_columns: ["subject_id", "hadm_id", "stay_id"]
primary_algorithm: "seven core features; median imputation; Z-score standardization; direct K-means in seven-dimensional scaled space (K=3)"
primary_external_criterion: "in-hospital mortality; follow-up start TBD"
confidence_level: 0.95
software:
  language: "Python and GoogleSQL"
  package_versions_lock: "TBD"
  random_seed_policy: "base seed 42; deterministic derived seeds for resampling"
```

## 1. 分析定位

本 SAP 规范当前 MIMIC-IV 开发表型分析。由于研究结果在本文件形成前已经被访问，所有分析均按探索性处理。K=3、当前七项特征、部分敏感性分析和回归模型不得描述为揭盲前预设。未来确认性验证应使用独立数据和单独冻结的方案。

本 SAP 优先约束未来重跑和论文解释；当它与当前代码不一致时，不静默追认代码行为，而在“实现差异与冻结阻塞项”中明确列出。

## 2. 分析人群与粒度

### 2.1 Cohort sets

| 分析集 | 草案定义 | 用途 |
|---|---|---|
| 宽表队列 | 成人 non-traumatic SAH、每次住院首次 ICU stay、ICU LOS ≥24h | flow 与缺失审计 |
| 当前 phenotype discovery set | 宽表队列 + 七变量缺失≤2 + 排除 0–24h 大量 RBC | 当前代码的主聚类 |
| 推荐 outcome landmark set | discovery set 中 48h 时仍存活且未出院者 | 严格的 48h 后院内死亡关联；尚未实现 |
| 48h LOS sensitivity | discovery 条件 + ICU LOS ≥48h | 完整观察机会敏感性 |
| no-RBC sensitivity | discovery 条件 + 0–48h 无记录 RBC | 治疗污染敏感性 |
| complete-case sensitivity | 七项核心变量均完整 | 插补依赖敏感性 |
| strict aneurysm-evidence sensitivity | 破裂动脉瘤性 SAH 诊断或动脉瘤处置证据 | 病因特异性敏感性 |

当前每次住院可贡献一个 stay，同一患者可能重复。冻结前应优先选定每位患者首次符合条件住院；若保留重复住院，则所有重采样、训练/验证划分和稳健方差必须以 `subject_id` 为最高依赖单位。

### 2.2 Flow counts

在不输出患者级值的前提下记录每一步的 stays、admissions 和 distinct subjects：

1. 所有 SAH 诊断住院；
2. 成人；
3. 排除明确创伤性 SAH；
4. 有 ICU stay；
5. 每次住院首次 ICU stay；
6. ICU LOS ≥24h；
7. 七项核心变量缺失≤2；
8. 主分析排除 0–24h 大量输血；
9. 不排除大量输血敏感性人群；
10. 其他敏感性人群。

## 3. 变量和时间

### 3.1 主聚类变量

| Feature | Summary | Transform | Direction used only for phenotype ordering |
|---|---|---|---:|
| `gcs_motor_min_48h` | minimum in [0,48h) | none | −1 |
| `map_min_48h` | minimum in [0,48h) | none | −1 |
| `shock_index_max_48h` | maximum in [0,48h) | none | +1 |
| `spo2_min_48h` | minimum in [0,48h) | none | −1 |
| `creatinine_max_48h` | maximum in [0,48h) | none | +1 |
| `sodium_max_48h` | maximum in [0,48h) | none | +1 |
| `platelet_min_48h` | minimum in [0,48h) | none | −1 |

方向仅用于在聚类后把 raw labels 排成 P1、P2、P3，不参与 K-means 距离。严禁用死亡率为 cluster 重新排序或选择 K。

### 3.2 主要结局

`hospital_mortality = hospital_expire_flag`。在冻结 follow-up start 前，结果只能称为全住院描述性关联。若采用推荐的 48h landmark，则：

- 纳入 48h 时仍住院且存活者；
- `followup_start = icu_intime + 48h`；
- 结局为 landmark 后、该次出院前死亡；
- 48h 前死亡/出院者不属于该目标人群，并单独报告其数量和特征。

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
3. 验证临床范围过滤与单位：GCS motor、MAP、HR/SBP、SpO2、creatinine、sodium、platelet。
4. 审计 sodium label/unit，排除非血清/血浆 sodium assay 混入。
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

1. 仅纳入七项核心变量最多缺失两项的 stays。
2. 每列以 discovery set 中位数单次插补。
3. 插补后用 discovery set 均值和标准差做 Z-score。

该方法适用于探索性聚类的可复现主分析，但不表达缺失机制已被消除。

### 5.3 防泄漏与重采样

在任何 bootstrap、内部验证或分区分析中，插补器、scaler 和聚类模型必须在每个重采样训练集内重新拟合，再将未抽中/评估记录投影到该模型。不得在全数据上先固定 imputer/scaler 后只重采样 K-means。

同一 `subject_id` 的全部 stays 必须进入同一重采样单位或同一数据分区。

### 5.4 缺失敏感性分析

- 完整病例重复完整主流程。
- 缺失数≤1 子集（若实现）。
- 可选多重插补仅作为结构敏感性：在每个插补数据集重跑聚类，通过共识矩阵比较；不得简单 Rubin 合并 cluster labels。

## 6. 主表型分析

### 6.1 预处理和输入空间

按以下固定顺序执行：

1. 选择七项核心变量；
2. 中位数插补；
3. Z-score 标准化；
4. 在七维标准化空间直接运行 K-means。

保存并报告 imputation medians、scaler means/SDs、七维 K-means centroids 和软件版本，以支持 frozen transport。

### 6.2 K-means 参数

```yaml
n_clusters: 3
random_state: 42
n_init: 100
input_space: "seven standardized core features (direct 7D K-means)"
```

K=3 是结果访问后锁定的探索性主方案。对 K=2–5 报告 inertia、silhouette、Calinski–Harabasz、Davies–Bouldin、最小 cluster N 和比例，但不得以院内死亡梯度选择 K。

K=4 仅作为高分辨率探索性敏感性，不得替换 K=3，除非另行修订方案并明确结果知情。

### 6.3 表型排序与命名

按七项标准化中心的预定义不良方向求和，形成不使用结局的 `severity_score`，据此将 cluster 排为 P1–P3。报告 raw labels 与 ordered labels 映射。

在独立验证前使用 P1/P2/P3 或纯描述性名称。若某一表型稳定性不足或边界重叠明显，不赋予确定的临床亚型名称。

## 7. 聚类质量与稳定性

### 7.1 必报指标

- 各 phenotype 的 N 和比例；
- silhouette、Calinski–Harabasz、Davies–Bouldin；
- 200 次按 `subject_id` 的 bootstrap/subsampling；
- 每次重拟合完整 median imputation + Z-score + direct 7D K-means；
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

当前代码未按患者重采样、未在 bootstrap 内重拟合完整 imputation/scaling/K-means，也未计算 cluster-wise Jaccard；这是冻结阻塞项。

## 8. 描述与外部判据

按 phenotype 报告连续变量 median [IQR]，分类变量 n (%)。对于聚类输入变量，组间差异是聚类构造的一部分，不作为独立假设发现。主要展示：

- 七项原始特征 profile 和标准化 heatmap；
- 年龄、性别、race group、admission type、aneurysm evidence；
- 贫血、RBC、过程性治疗和严重程度评分；
- 院内死亡及 95% CI。

极小单元格按机构披露规则抑制，不在图中显示患者级散点。

## 9. 主要关联模型

### 9.1 Primary outcome association

在 follow-up start 冻结后，拟合 logistic regression：

```text
hospital_mortality ~ C(phenotype) + age + C(gender)
                     + C(admission_type_group)
                     + C(nsah_evidence_level)
```

若 `nsah_evidence_level` 在分析人群中无变异则删除。P1 为参考，报告 P2 vs P1、P3 vs P1 的 OR、95% CI 和 P 值，并同时报告未调整模型。该模型估计条件性、非因果性关联。

`has_aneurysm_dx`、`has_aneurysm_procedure` 与 evidence level 可能重复编码，冻结前应选定一个一致的诊断严重度表示，不能按拟合结果逐项挑选。

### 9.2 Anemia analysis

Hb 不属于当前七项 phenotype 输入，但贫血仍是结果访问后的探索性变量，以下分析分层解释：

1. 主表型中的 anemia rate：描述性。
2. `phenotype + anemia` 模型：探索性、非因果性关联。
3. phenotype × anemia interaction：仅在各交叉格事件充足时报告；必须报告 interaction test，不用分层显著/不显著差异推断效应修饰。

不将 anemia 分层结果解释为输血治疗指征或治疗效果异质性。

### 9.3 模型诊断和 fallback

- 报告每个模型 N、events、参数自由度和收敛状态。
- 检查完全/近完全分离、极端标准误、影响点和连续年龄线性假设。
- 年龄非线性敏感性使用限制性立方样条（结点方案冻结后实施）。
- 若稀疏或不收敛，减少非核心协变量或使用 Firth/惩罚 logistic；不得只报告成功模型。
- 不以固定“10 EPV”作为充分性证明；按 CI 宽度、事件数和参数自由度判断信息量。

## 10. 次要与探索性模型

- ICU mortality logistic：次要、探索性。
- LOS：因死亡截断，仅描述 median [IQR]；正式比较需预先指定 survivor-only 或 competing-event estimand。
- KM/Cox：活着出院是竞争事件，当前简单删失分析只作可视化/探索。若用于推断，预设 cumulative incidence 和 cause-specific hazard 或合适 competing-risk 方法。
- 预测增量：GCS-only、连续七变量、phenotype-only 等仅为探索性描述；按 `subject_id` 分组的交叉验证，在每折内拟合全部 preprocessing。不得把 phenotype 研究改写为已验证预测模型。
- 线性 logistic SHAP-style approximation：只解释死亡模型贡献，不解释 cluster assignment 或病因机制。
- 0–48h 过程性治疗固定协变量模型：因时间依赖和 immortal-time/collider 风险，仅探索性，不进入主要结论。

## 11. 多重性

```yaml
hypothesis_hierarchy:
  primary:
    - "K=3 phenotype structure, size and stability（无单一假设检验）"
    - "P2/P3 versus P1 与院内死亡的探索性总体关联"
  secondary:
    - "ICU mortality and independent severity-score gradients"
    - "anemia association"
  exploratory:
    - "phenotype × anemia interaction"
    - "pairwise phenotype comparisons"
    - "process-of-care, survival, prediction and SHAP-style analyses"
    - "K=4 and alternative algorithms/features"
control_method: "所有结果知情分析以效应量和 CI 为主；同一结局的 pairwise phenotype 比较用 Holm；成组次要特征检验用 Benjamini–Hochberg FDR；未校正探索性结果明确标注。"
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
total_stays: TBD
unique_admissions: TBD
unique_subjects: TBD
subjects_with_repeated_admissions: TBD
primary_analysis_stays: TBD
landmark_analysis_stays: TBD
hospital_deaths_total: TBD
hospital_deaths_after_landmark: TBD
phenotype_sizes: TBD
minimum_phenotype_fraction: TBD
bootstrap_effective_subjects: TBD
missingness_by_feature: TBD
```

可行性判断包括：最小 cluster 的绝对 N/比例、bootstrap 置信范围、每个死亡模型的事件数与自由度、OR CI 宽度以及 phenotype × anemia 交叉格事件数。任何事件稀疏的亚组只报告粗率和宽 CI，不作稳定调整估计。

## 13. 敏感性分析矩阵

| 风险/假设 | 预设替代 | 稳健性解释 |
|---|---|---|
| 48h 治疗污染 | 同源 0–24h 特征流程 | 表型中心和死亡关联方向大体一致；不要求标签逐例相同 |
| 观察机会不等 | ICU LOS ≥48h；48h landmark | 明确目标人群变化，报告被排除早期事件 |
| RBC 改变 Hb/循环 | 无 RBC 子集；输血前 Hb；不排除大量输血版本 | 若结构明显改变，承认治疗敏感性，不作本质化命名 |
| 单次中位数插补 | complete case；缺失≤1；可选多重插补共识 | 报告 ARI、中心漂移和 cluster size |
| GCS 表征 | total GCS、GCS grade 替换/加入 | 报告 ARI 和结局梯度，不按结果选择版本 |
| 病因异质性 | strict aneurysm-evidence subgroup | 仅评估可迁移方向，不把亚组重新称为主队列 |
| 算法假设 | hierarchical、GMM/LPA | 报告 ARI、entropy/BIC、cluster size；不按死亡率挑算法 |
| K 选择 | K=2–5 指标；K=4 exploratory | K=3 为结果知情锁定，其他 K 只展示结构敏感性 |
| 重复患者 | 每患者首次 admission；按 subject bootstrap | 若结果不同，优先报告患者独立方案 |
| 年龄模型形式 | age spline | 主要 phenotype contrast 方向和量级不应由线性假设决定 |
| 活着出院竞争 | cumulative incidence/cause-specific analysis | KM/Cox 仅支持性，不替代二元院内结局 |

### 13.1 不排除大量输血敏感性分析契约

`eligible_include_massive_transfusion_sensitivity = 1` 定义为七项核心变量缺失数 ≤2，不限制 `massive_transfusion_24h`。该版本只移除大量输血限制；预处理、七项核心变量、K=3、随机种子和结局定义与主分析保持一致，并在该敏感性样本内独立重拟合中位数插补、Z-score 标准化，并在七维标准化空间直接运行 K-means。

该分析为支持性而非共同主要分析。比较样本量、cluster size、原始特征谱、标准化中心、与主分析重叠 stays 的重叠 ARI 和结局关联方向，不按结果选择优先版本。若差异明显，结论应表述为表型结构对早期治疗敏感，并限制本质化命名；不得据此估计 RBC 输血因果效应。该规则在结局已访问后固定，不得描述为结果揭盲前预设。

## 14. 外部验证

当前 eICU 分析应描述为结果已访问后的探索性 external criterion/transport validation。Frozen transport 必须固定并发布以下 MIMIC 参数：

- feature definitions and clinical ranges；
- imputation medians；
- scaler mean/SD；
- K-means centroids；
- phenotype ordering map。

eICU 不得重新拟合这些参数后仍称为 frozen transport。De novo eICU clustering 仅是结构敏感性。若需要确认性外部验证，应创建独立 `study_id`、protocol、SAP、manifest 和冻结记录，且在再次查看其结局前锁定成功标准。

## 15. 输出清单

### 15.1 主文

1. Cohort flow diagram。
2. Table 1：非输入基线特征、输入特征 profile、缺失与过程性变量。
3. K=2–5 无监督指标和 K=3 选择说明。
4. K=3 phenotype heatmap、标准化中心与原始 median [IQR]。
5. Cluster size、bootstrap stability、Jaccard 和 assignment margin。
6. 院内死亡粗率及主要 logistic OR/95% CI。
7. 关键敏感性矩阵。

### 15.2 Supplement

- 完整 codebook、时间窗口和临床范围。
- 缺失模式与 measurement counts。
- K=4、24h、complete-case、strict aneurysm、no-RBC、LOS≥48h、不排除大量输血。
- GCS alternatives、GMM/LPA、hierarchical comparison。
- 预测、SHAP-style、KM/Cox 和过程性治疗探索结果。
- eICU frozen transport 参数与审计。

所有结果表必须通过小单元格和罕见组合披露审查。

## 16. 实现差异与冻结阻塞项

| SAP 要求 | 当前实现 | 冻结前动作 |
|---|---|---|
| 按患者处理重复结构 | 每住院首次 ICU，但患者可多次住院；bootstrap 按行 | 限定首次患者住院或按 subject_id 分组重采样 |
| 完整 pipeline bootstrap | 在固定的七维 scaled 空间重采样 K-means | 每次重拟合 imputer/scaler/K-means，并评估 OOB/投影稳定性 |
| Cluster-wise stability | 主要输出 ARI/same-label | 增加 Jaccard、assignment margin、多 seed |
| 明确 outcome follow-up start | 全住院死亡含 48h 前事件 | 实现 48h landmark 或降级为全住院描述性关联 |
| 48h 输入观察机会 | 主队列仅要求 LOS≥24h | 报告截短窗口；将 LOS≥48h/landmark 作为关键分析 |
| 主要回归规范 | 当前主调整模型同时含 phenotype 和 anemia，并动态加入重叠 aneurysm fields | 固定主要 formula；贫血保持探索性；统一 aneurysm covariate |
| Competing discharge | 当前 KM/Cox 将活着出院删失 | 降级为探索或实施 competing-risk 方法 |
| 多重性 | 当前脚本大量逐项 P 值，未统一校正 | 增加 Holm/FDR 输出和层级标签 |
| 样本量/事件依据 | 结果表存在但冻结契约未登记 | 在合规环境中填充 precision/event 表 |
| 环境和 artifact provenance | 未有正式 lock bundle | 建立 manifest、environment lock、deviations 和 protocol-sap-lock |
| Post-entry 大量输血排除 | 主分析保留排除；已增加 `eligible_include_massive_transfusion_sensitivity` 并接入 Python 敏感性流程 | 已实现；维持探索性解释并保留 deviation 记录 |

## 17. Go/no-go

- [x] 主要科学问题和 design family 已定义。
- [x] 主输入空间、算法和当前 K 已记录。
- [x] 结果访问状态真实标为 `accessed`。
- [ ] 治理决定覆盖真实数据处理环境。
- [ ] 数据 source manifest、access date 和 linkage provenance 完整。
- [ ] codebook 与 cohort version 已冻结。
- [ ] 重复患者规则和 subject-level resampling 已实现。
- [ ] outcome follow-up start、早期死亡/出院和竞争事件已冻结。
- [ ] 样本量、事件数、参数自由度和 precision 已记录。
- [ ] 缺失、稳定性和多重性计划已全部实现。
- [ ] 输出与代码通过独立复核。
- [ ] protocol/SAP hash、环境、commit、批准和 deviation log 齐全。

结论：`DRAFT_BLOCKED`。允许继续使用公开代码、合成数据或盲态 QC 开发；不得将当前文件描述为结果揭盲前冻结方案。

## 18. 版本历史

| Version | Date | Status | Summary |
|---|---|---|---|
| 0.1.0 | 2026-07-15 | DRAFT_BLOCKED | 根据现有实现重建 SAP；固定探索性定位并记录时间契约、患者依赖、bootstrap 和多重性缺口。 |
| 0.1.1 | 2026-07-16 | DRAFT_BLOCKED | 固定大量输血主/敏感性人群契约并记录结果已访问后的探索性实施；其他冻结阻塞项保持开放。 |
| 0.1.2 | 2026-07-16 | DRAFT_BLOCKED | 更正当前实现为七项特征、中位数插补、Z-score 后七维直接 K-means，并补充敏感性重叠 ARI 与特征谱输出契约。 |
