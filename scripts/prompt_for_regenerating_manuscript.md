# 论文生成提示词

## 使用方式

后续每次重新运行分析 pipeline 后，将以下内容发送给 Claude Code / Codex / Gemini，即可根据最新结果生成英文 + 中文论文、图表和 PDF。

```bash
claude ./scripts/prompt_for_regenerating_manuscript.md
```

## 提示词正文

````text
请根据最新研究结果完成 non-traumatic SAH 早期多模态生理表型论文的生成与更新。

默认读取：
- `dist/YYYYMMDD/analysis_result.md`，将 `YYYYMMDD` 替换为当前执行日期。
- 如 `analysis_result.md` 信息不足，可只读查询 BigQuery 结果表：
  - `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
  - `phenotype_k_selection_metrics`
  - `phenotype_cluster_assignments`
  - `phenotype_cluster_centers_zscore`
  - `phenotype_outcome_summary`
  - `phenotype_anemia_feasibility`
  - `phenotype_regression_models`
  - `phenotype_prediction_metrics`
  - `phenotype_bootstrap_stability`
  - `phenotype_baseline_characteristics`
  - `phenotype_process_of_care_audit`
  - `phenotype_process_of_care_adjusted_models`
  - `phenotype_survival_km_curve`
  - `phenotype_survival_logrank`
  - `phenotype_survival_cox_models`
  - `phenotype_log_pca_kmeans_sensitivity`
  - `phenotype_log_pca_kmeans_loadings`
  - `phenotype_log_pca_kmeans_bootstrap_stability`
  - `phenotype_raw_kmeans_outcome_summary_sensitivity`
  - `phenotype_raw_kmeans_bootstrap_stability_sensitivity`
  - `phenotype_complete_case_sensitivity`
  - `phenotype_hb_free_sensitivity`
  - `phenotype_inr_free_sensitivity`
  - `phenotype_sensitivity_cohort_summary`
  - `phenotype_gcs_sensitivity_summary`
  - `phenotype_epvs_sensitivity_summary`
  - `phenotype_candidate_feature_audit`
  - `phenotype_k3_k4_refinement_crosstab`

除非结果表已明确更新，不得编造数据。所有数字必须与最新 `analysis_result.md` 或 BigQuery 表一致。

## 0. 研究定位和写作边界

这篇论文的主定位是：

> 在 critically ill adults with non-traumatic SAH 中，利用 ICU 入科后 0-48 小时常规多模态生理数据识别早期临床可解释 phenotype，并评估其死亡风险、贫血负担和外部严重度一致性。

必须避免以下过度表述：
- 不要声称早期贫血是独立因果危险因素。
- 不要声称某个 phenotype 需要输血或可从输血获益。
- 不要把本研究写成 treatment effect / causal inference / transfusion strategy 研究。
- 不要声称 PCA 保留了大部分信息；目前 3 个 PC 解释方差约 56%，必须透明报告。
- 不要说 phenotype 是 SOFA 划分出来的；SOFA/SAPSII/OASIS/LODS 是外部验证变量，不是聚类输入。
- 不要把过程性治疗、器官支持或 Cox/KM 结果写成 causal treatment effect。`phenotype_process_of_care_*` 和 `phenotype_survival_*` 是描述性/敏感性分析，用来说明治疗过程和住院期死亡时间分布，不是干预获益证据。
- 不要把 0-48h 内血管活性药、机械通气、RBC 输注、CRRT 等过程治疗变量作为 Cox 主模型的固定 baseline 协变量来做因果解释；这会有 immortal time bias 风险。若正式纳入生存模型，应建模为 time-varying covariates；当前固定协变量 Cox 只能写成 exploratory sensitivity association。

核心结论边界：
- 早期贫血定义为 ICU 入科后 0-48 小时最低 Hb <10 g/dL。
- 早期贫血明显富集于高危 phenotype；“调整 phenotype 后是否独立”必须优先引用 `phenotype_hb_free_anemia_regression`，因为主 phenotype 本身包含 Hb，直接调整主 phenotype 会产生过度调整/循环论证。
- 贫血更适合解释为多系统生理失衡 phenotype 的组成特征和风险标志。
- 过程性治疗和器官支持变量必须作为重要结果报告：nimodipine、EVD/ICP、vasopressor、mechanical ventilation、RBC transfusion、CRRT、fluid balance 及过程性治疗调整模型。它们只能解释为 severity/treatment-selection/context markers，不得作为治疗效果结论。

## 0.1 高分论文写作标准

生成 manuscript 前必须先阅读并遵循：

`docs/high_impact_manuscript_standards.md`

该标准规定了高分医学论文的总体叙事、Methods 透明度、Results 组织方式、Discussion 结构、图表/表格设计、审稿反击和语言风格。本 prompt 只补充本研究的项目特异性结果、变量、结论边界和输出文件要求。

本研究的项目特异性关键词：
- non-traumatic subarachnoid hemorrhage
- critical care
- physiological phenotypes
- unsupervised learning
- anemia
- coagulation
- SOFA
- MIMIC-IV

## 1. 创建目录与记录生成模型

创建 `dist/YYYYMMDD` 目录。

在 `dist/YYYYMMDD/readme.txt` 中写明：
- markdown 和 pdf 文件由哪个模型生成；
- 生成日期；
- 使用的主要输入文件；
- 是否直接查询了 BigQuery。

## 2. 更新图表

运行作图脚本生成 PNG 图，传入当前日期文件夹作为参数：

```bash
python3 scripts/generate_manuscript_figures.py YYYYMMDD
````

如果最新数据与脚本硬编码数值不一致，先根据 `dist/YYYYMMDD/analysis_result.md` 或 BigQuery 结果表更新 `scripts/generate_manuscript_figures.py`，再运行。

推荐图表清单：

- `fig1_cohort_flowchart.png`：STROBE-style 队列筛选流程图。必须尽量显示每一步人数，包括初筛 MIMIC-IV ICU/SAH 记录、adult non-traumatic SAH、first ICU stay、ICU LOS >=24h、排除 traumatic SAH、排除 24h massive transfusion、最终 eligible primary analysis cohort。若 `analysis_result.md` 未提供某一步人数，不得编造；应在图或图例中明确“not available in current output”，并在正文说明需要 pipeline 输出筛选计数。
- `fig2_primary_log_pca_heatmap.png`：主 log-PCA K=3 phenotype 的标准化中心热图。
- `fig3_outcomes_anemia.png`：P1/P2/P3 住院死亡率、ICU 死亡率、早期贫血率、RBC 输注率。
- `fig4_external_severity_validation.png`：SOFA、SAPS II、APS III、OASIS、LODS 随 phenotype 的梯度。
- `fig5_prediction_performance.png`：GCS-only、phenotype-only、phenotype+covariates、8-features 的 AUROC/Brier。
- `fig_s1_k_selection.png`：log-PCA 主方案与 raw K-means 敏感性方案的 K=2-5 指标。
- `fig_s2_bootstrap.png`：主 log-PCA bootstrap ARI 和最小簇大小。
- `fig_s3_sensitivity_summary.png`：raw K-means、complete-case、Hb-free、INR-free、no-RBC、ICU LOS >=48h、GCS alternatives 的敏感性汇总。
- `fig_s4_k4_refinement.png`：K=3/K=4 交叉分布。
- `fig_s5_pca_loadings.png`：PC1-PC3 loadings，突出 INR、creatinine、Hb、GCS、shock index 等贡献。
- `fig_s6_forest_plot.png`：调整后死亡 OR，包括 phenotype、early anemia、SOFA-adjusted 模型（若已生成）。
- 如作图脚本支持，新增 `fig_s7_hospital_survival.png` 或同等图：按 phenotype 展示住院期 Kaplan-Meier/累积死亡曲线，并在图例或正文报告 pairwise log-rank。若脚本暂不支持，正文和表格仍必须报告 `phenotype_survival_logrank` / `phenotype_survival_cox_models` 的关键结果。

若脚本暂时只支持旧 8 图，请至少更新旧图中的数据和标题，确保主方案写成 log-PCA K=3，不再把 raw K-means 当主方案。

图表叙事和表格组织标准见 `docs/high_impact_manuscript_standards.md`。本研究至少应包含：

- Table 1：Baseline characteristics by phenotype。不得只列年龄、LOS、贫血、输血和死亡；应尽量包含 demographics、admission type、non-traumatic SAH evidence level、aneurysm diagnosis/procedure、SOFA/SAPS II/APS III/OASIS/LODS、mechanical ventilation、vasopressor、EVD/ICP、nimodipine、RBC transfusion、CRRT、hospital/ICU outcomes 等。若某变量未在当前结果表中出现，可省略但要优先从 `phenotype_baseline_characteristics` 和 process-of-care summary 中补齐。
- Table 2：Early physiological profiles by phenotype。
- Table 3：Outcome models。
- Table 4：Process-of-care and hospital-course models。必须汇总 `phenotype_process_of_care_adjusted_models` 与 `phenotype_survival_cox_models` 的核心 phenotype OR/HR，不得只写主 logistic 模型。Cox 表中 `cox_phenotype_process_of_care_exploratory` 必须标注 immortal time bias 风险和 exploratory sensitivity association。
- Supplementary Table 1：K selection and clustering diagnostics。
- Supplementary Table 2：Sensitivity analyses。
- Supplementary Table 3：Process-of-care distribution by phenotype。来自 `phenotype_process_of_care_audit`，至少包含 nimodipine、EVD/ICP、vasopressor、mechanical ventilation、RBC transfusion、CRRT、fluid balance。
- Supplementary Table 4：PCA loadings。
- Supplementary Table 5：Cohort definition / ICD code and exclusion algorithm。若当前结果没有 ICD code 明细，应在 Methods 明确代码定义位于 SQL/pipeline，并在补充表中写“code list to be supplied from cohort SQL”，不要伪造 ICD code。

## 3. 更新英文论文

更新 `dist/YYYYMMDD/manuscript_non_traumatic_sah_phenotypes.md`。

### 3.1 标题

使用以下标题：

**Early Multimodal Physiological Phenotypes and Outcomes in Critically Ill Adults With Non-Traumatic Subarachnoid Hemorrhage: A Retrospective Cohort Study Using MIMIC-IV 3.1**

不要使用 “Beyond GCS” 或夸张 AI 标题。

### 3.2 文章结构

按以下结构写：

1. Abstract
2. Introduction
3. Methods
4. Results
5. Discussion
6. Conclusions
7. References
8. Tables
9. Supplementary Tables

图表嵌入正文对应位置，不要全部堆在文末。每张图后紧跟：

```markdown
**Figure X.** 图例文字。
```

### 3.3 Abstract 必须包含

Background：

- non-traumatic SAH ICU 患者异质性大；
- 传统 GCS/SOFA 等评分无法完全表达早期多系统生理模式。

Methods：

- MIMIC-IV 3.1；
- adult non-traumatic SAH ICU patients；
- 0-48h early physiology；
- 8 个预设变量：minimum Hb、minimum GCS motor、minimum MAP、maximum shock index、minimum SpO2、maximum creatinine、maximum INR、minimum platelet；
- creatinine 和 INR 做 log1p；
- Z-score 标准化；
- PCA 取 3 个 PC；
- K-means K=3；
- primary outcome = hospital mortality；
- sensitivity analyses = raw K-means、complete-case、Hb-free、Hb-free anemia regression、INR-free、no-RBC、ICU LOS >=48h、GCS alternatives、K=4、process-of-care adjustment、hospital-course Cox/KM。

Results：

- N 必须使用最新结果，目前为 `1,186`；
- hospital deaths 目前为 `235`，overall mortality `19.8%`；
- P1/P2/P3 当前主 log-PCA 结果：
  - P1: n=696, hospital mortality 6.5%, early anemia 12.1%
  - P2: n=382, hospital mortality 32.5%, early anemia 41.6%
  - P3: n=108, hospital mortality 61.1%, early anemia 66.7%
- log-PCA K=3 silhouette 约 0.334；
- raw K-means K=3 silhouette 约 0.224；
- log-PCA bootstrap mean/median ARI 约 0.919/0.926；
- phenotype adjusted OR 显著；
- early anemia adjusted OR 不显著；
- SOFA/SAPSII/OASIS/LODS 随 phenotype 递增。
- process-of-care adjusted logistic models attenuate but do not remove phenotype mortality associations；
- hospital-course log-rank and Cox models show persistent phenotype gradients；必须明确 alive discharges censored at hospital discharge。

Conclusions：

- 早期多模态生理 phenotype 能识别不同死亡风险层级；
- P3 是多系统失衡高危表型；
- 贫血富集于高危 phenotype，但更像系统性失衡标志，而非独立因果因素。

### 3.4 Introduction 写作要点

三段式：

1. non-traumatic SAH ICU 患者死亡风险高，异质性大，预后不仅取决于神经损伤，也受循环、氧合、肾功能、凝血、贫血影响。
2. 传统 GCS/WFNS/SOFA 有用，但不能表达 ICU 早期多系统生理组合；早期贫血在 SAH 中常见，但其是否为独立危险因素或高危状态标志不清楚。
3. 本研究目标：
   - 识别 early multimodal physiological phenotypes；
   - 比较 mortality 和 severity score；
   - 探索 early anemia 在 phenotype 中的分布和预后意义。

### 3.5 Methods 写作要点

必须写清楚：

**Data source**

- MIMIC-IV 3.1；
- BigQuery；
- retrospective cohort；
- de-identified data。

**Cohort**

- adult；
- non-traumatic SAH ICD；
- 必须列明 ICD-9/ICD-10 non-traumatic SAH 纳入 code、traumatic SAH 排除 code、massive transfusion 排除规则和 adult/first ICU stay 的操作定义；如果 manuscript 不能完整列在正文，应放入 Supplementary Table 5。不得只写“ICD-defined”而不提供可复现 code/algorithm。
- first ICU stay；
- ICU LOS >=24h；
- traumatic SAH excluded；
- massive transfusion within 24h excluded；
- aneurysm diagnosis/procedure only used as evidence/covariate/sensitivity, not mandatory inclusion。
- Figure 1 必须尽量给出每一步筛选人数；如果当前 pipeline 没有导出全部筛选人数，应在 Limitations 或 Methods 中说明当前 flow count granularity 的限制，并建议 pipeline 后续输出完整 STROBE flow counts。

**Time window**

- T0 = ICU intime；
- primary physiology window = 0-48h；
- ICU LOS >=48h 敏感性；
- 24h window 如未完成，列为 future sensitivity / planned analysis，不要编造结果。

**Feature selection**
表格列出 8 个变量、聚合方式和生理维度：

- minimum Hb: anemia
- minimum GCS motor: neurological impairment
- minimum MAP: perfusion
- maximum shock index: circulatory stress
- minimum SpO2: oxygenation
- maximum creatinine: renal dysfunction
- maximum INR: coagulation
- minimum platelet: platelet/coagulation

说明：

- lactate、PaO2/FiO2、troponin 因缺失或选择性检测不纳入主聚类；
- sodium 只作为描述/敏感性候选，不进入主聚类；
- SOFA/SAPSII/OASIS/LODS 不进入聚类，只作外部验证。

**Clustering**

- 对 creatinine 和 INR 取 `log1p`；
- 中位数填补；
- Z-score 标准化；
- PCA 取 3 个 PC；
- K-means；
- 必须写清 PCA 和 K-means 的可复现参数：输入变量顺序、变量方向是否反转或仅按原始临床方向解释、imputation 在全分析样本内完成、standardization 方法、PCA solver（如结果表/脚本可得）、K-means random seed、n_init、max_iter、以及 phenotype ordering/renaming 规则。若某参数只在脚本中可见，按脚本记录；若不可得，标记为 not reported by current pipeline，不得编造。
- K=3 为主分型；
- K=4 为高分辨率探索；
- raw K-means 为敏感性参照；
- 3 个 PC 的解释方差必须报告，当前约 56.4%。

**Anemia definition**

- Early anemia = minimum Hb <10 g/dL within 0-48h after ICU admission。
- `early_anemia_all` 是主定义。
- `early_anemia_pre_transfusion`、Hb <7、Hb <12 可作为敏感性计划/补充，若无结果不要编造。

**Statistical analysis**

- Kruskal-Wallis / chi-square；
- adjusted logistic regression；
- phenotype × anemia interaction；
- prediction models with cross-validation；必须说明 cross-validation 折数、是否 stratified、评价指标 AUROC/Brier、是否为预测性能描述而非临床部署模型。
- bootstrap ARI；必须说明 bootstrap resample 次数、ARI 参照对象、最小簇大小统计方式。
- sensitivity analyses；
- external severity validation；
- SOFA-adjusted exploratory models，如已正式生成结果表则报告；若只是临时分析，应写为 exploratory and not prespecified。
- process-of-care adjusted logistic models：必须说明这些变量包括 aneurysm securing、nimodipine、EVD/ICP、vasopressor、mechanical ventilation、RBC transfusion、CRRT、fluid balance；必须写明这些变量可能是 downstream markers/mediators，模型仅为 sensitivity adjustment，不是 causal control。
- hospital-course survival analyses：必须说明 Kaplan-Meier / log-rank / Cox 的时间尺度、结局、删失规则（alive discharge censored at discharge）和模型层级（unadjusted、clinical adjusted、process-of-care adjusted）。

Methods 中还必须明确：

- 聚类是 unsupervised；hospital mortality、SOFA、SAPSII、OASIS、LODS、RBC transfusion 均未作为聚类输入。
- 过程性治疗和器官支持变量也未作为聚类输入；它们只用于 Table 1/补充表描述、过程性治疗敏感性模型和住院期 time-to-event 补充分析。
- phenotype 命名是在聚类完成后基于标准化中心和原始中位数解释，不是先验人工规则。
- K=3 不是单纯按 silhouette 最大选择；选择理由是临床可解释性、最小簇样本量、风险梯度、bootstrap 稳定性和敏感性分析综合判断。
- K=2 代表粗略低/高风险二分，K=4 代表高分辨率探索但小簇较小；二者均不作为主方案。
- 任何 SOFA-adjusted 模型如果未被 pipeline 正式写入结果表，必须标记为 exploratory post hoc，不得作为主验证结论。
- 参考文献不能只有 MIMIC/STROBE/TRIPOD。必须补充 SAH 临床分级/预后、贫血与 SAH/ICU、ICU phenotyping/unsupervised clustering、K-means/PCA 或 cluster reporting 相关文献。若无法联网核对，不得伪造具体文献；应保留“references to be completed”标记并在 final report 中说明。

### 3.6 Results 写作顺序

按以下顺序写，不要按脚本输出顺序写：

1. Cohort and feature availability
   - N=1186；
   - deaths=235；
   - early anemia=315；
   - RBC transfusion 48h rate 约 2.0%；
   - INR missing 5.5%，creatinine missing 0.08%，其他核心变量无缺失；
   - troponin/lactate/PaO2-FiO2 缺失高，不进入主聚类。

2. Primary log-PCA K=3 solution
   - P1/P2/P3 样本量、死亡率、贫血率；
   - 临床命名：
     - P1: physiologically stable / low-risk phenotype
     - P2: neurological impairment and circulatory stress phenotype
     - P3: multisystem derangement phenotype
   - 必须解释为什么 K=3 是主方案：
     - K=2 silhouette 较高但只能粗分低/高危；
     - K=4 silhouette 略高但小簇更小，解释和后续建模不稳；
     - K=3 在风险梯度、样本量和临床解释之间最平衡。

3. Raw clinical characteristics
   - 用原始中位数描述：
     - P1: Hb ~11.7, GCS motor 6, MAP ~64, shock index ~0.82, SpO2 ~92, creatinine ~0.8, INR ~1.1, platelet ~204
     - P2: Hb ~10.20, GCS motor 1, MAP ~58, shock index ~1.00, SpO2 ~94, creatinine ~0.9, INR ~1.2, platelet ~174
     - P3: Hb ~8.85, GCS motor 1, MAP ~55, shock index ~1.16, SpO2 ~88.5, creatinine ~1.9, INR ~1.8, platelet ~92
   - 数值必须与最新表一致，若有变化按最新结果改。

4. External severity validation
   - SOFA/SAPSII/APSIII/OASIS/LODS 不作为输入，但随 phenotype 增加。
   - 当前 SOFA median:
     - P1 2 [1,3]
     - P2 4 [2,6]
     - P3 8 [5,11]
   - 强调这是 external validation，不是聚类依据。
   - 如果报告 SOFA-adjusted model，必须写成“phenotype 仍与死亡相关，说明其不只是 SOFA 复制品”；同时承认 SOFA 与 phenotype 高度相关，不能过度声称完全独立。

5. Anemia analyses
   - 贫血率梯度；
   - phenotype 内贫血事件数；
   - adjusted anemia main effect 不显著；
   - phenotype × anemia interaction 不显著；
   - 不要解释为贫血保护或输血策略。

6. Prediction
   - GCS-only AUROC 约 0.54；
   - phenotype-only AUROC 约 0.75；
   - phenotype + anemia + covariates AUROC 约 0.80；
   - 8 raw features AUROC 约 0.84；
   - phenotype 的价值是简化和解释，不是替代全部原始变量。

7. Process-of-care, organ support, and hospital-course survival analyses
   - 这一节必须写入正文，不得只放补充材料。
   - 使用 `phenotype_process_of_care_audit` 报告过程性治疗/器官支持分布：
     - nimodipine 48h：overall 675/1186 (56.9%)；P1 434/696 (62.4%)；P2 224/382 (58.6%)；P3 17/108 (15.7%)。
     - EVD/ICP 48h：overall 322/1186 (27.2%)；P1 121/696 (17.4%)；P2 186/382 (48.7%)；P3 15/108 (13.9%)。
     - vasopressor 48h：overall 252/1186 (21.2%)；P1 43/696 (6.2%)；P2 154/382 (40.3%)；P3 55/108 (50.9%)。
     - mechanical ventilation 48h：overall 431/1186 (36.3%)；P1 122/696 (17.5%)；P2 247/382 (64.7%)；P3 62/108 (57.4%)。
     - RBC transfusion 48h：overall 24/1186 (2.0%)；P1 3/696 (0.4%)；P2 13/382 (3.4%)；P3 8/108 (7.4%)。
     - CRRT 48h：overall 10/1186 (0.8%)；P1 0/696 (0.0%)；P2 1/382 (0.3%)；P3 9/108 (8.3%)。
     - fluid balance 48h median：overall 1.38 L [-0.45, 2.96]；P1 0.94 [-0.65, 2.26]；P2 2.26 [0.21, 3.80]；P3 2.41 [-0.04, 6.19]。
   - 使用 `phenotype_process_of_care_adjusted_models` 报告递进模型：
     - process_model_3_specialty_care：P2 vs P1 OR 6.25 (95% CI 4.11-9.49)；P3 vs P1 OR 17.39 (95% CI 9.87-30.65)；nimodipine OR 0.48 (95% CI 0.31-0.74)；EVD/ICP OR 1.81 (95% CI 1.15-2.83)。
     - process_model_4_organ_support：P2 vs P1 OR 3.88 (95% CI 2.48-6.06)；P3 vs P1 OR 11.75 (95% CI 6.37-21.68)；nimodipine OR 0.51 (95% CI 0.32-0.81)；vasopressor OR 2.61 (95% CI 1.72-3.95)；mechanical ventilation OR 2.11 (95% CI 1.40-3.19)；RBC transfusion OR 0.39 (95% CI 0.13-1.18)。
   - 对上述模型的解释必须谨慎：过程性治疗变量可能是 severity marker、treatment selection marker 或 mediator，不能写成“治疗保护/有害”或“调整后证明表型独立于治疗”。
   - 使用 `phenotype_survival_logrank` 报告住院期 pairwise log-rank：
     - P1 vs P2 p=1.44e-17；
     - P1 vs P3 p=1.68e-30；
     - P2 vs P3 p=2.28e-05。
   - 使用 `phenotype_survival_cox_models` 报告 Cox：
     - unadjusted Cox：P2 HR 4.10 (95% CI 2.91-5.79)；P3 HR 7.78 (95% CI 5.29-11.45)。
     - clinical adjusted Cox：P2 HR 4.35 (95% CI 3.05-6.21)；P3 HR 8.55 (95% CI 5.51-13.29)。
     - process-of-care adjusted Cox：P2 HR 2.99 (95% CI 2.03-4.40)；P3 HR 5.14 (95% CI 3.20-8.26)；nimodipine HR 0.60 (95% CI 0.41-0.86)；vasopressor HR 2.14 (95% CI 1.56-2.92)；mechanical ventilation HR 1.82 (95% CI 1.31-2.53)；RBC transfusion HR 0.41 (95% CI 0.17-1.01)。
   - Cox/KM 结果必须写成 “hospital-course association / time-to-event sensitivity analysis”，不要写成长期生存或出院后生存。

8. Sensitivity analyses
   - raw K-means 方向一致；
   - complete-case 方向一致；
   - Hb-free 方向一致，反驳 Hb 循环论证；
   - INR-free 不改善 silhouette，支持保留 INR；
   - no-RBC 和 ICU LOS >=48h 方向一致；
   - GCS alternatives 改变 assignment，说明神经变量选择重要，GCS motor 需说明是预设且低缺失；
   - K=4 作为探索性高分辨率分型。
   - 敏感性分析的总结必须围绕“是否支持主结论”而不是逐项报流水账。

### 3.7 Discussion 必须包含的论点

按 6 段组织：

1. Principal findings：
   - 3 个早期 phenotype；
   - 显著死亡率梯度；
   - P3 是多系统失衡；
   - anemia 富集但非独立因果。

2. Clinical interpretation：
   - P1: physiologically stable low-risk；
   - P2: neurological impairment + circulatory stress；
   - P3: multisystem derangement with anemia, coagulopathy, renal dysfunction, hypoxemia, thrombocytopenia。

3. Relationship with SOFA/severity scores：
   - severity scores were not clustering inputs；
   - their gradient validates phenotypes；
   - phenotype is not a SOFA clone；
   - if SOFA-adjusted model is available, mention phenotype remains associated with mortality after SOFA adjustment。

4. Early anemia interpretation：
   - anemia is phenotype-enriched；
   - adjusted anemia effect not significant；
   - anemia likely marker/component of systemic derangement；
   - no transfusion treatment conclusion.

5. Process-of-care and survival interpretation：
   - P2 has high EVD/ICP and mechanical ventilation use, matching neurological impairment；
   - P3 has higher vasopressor, RBC, CRRT and fluid-balance burden, matching multisystem derangement；
   - process-of-care adjustment attenuates but does not eliminate phenotype associations；
   - KM/log-rank/Cox results support hospital-course risk separation；
   - because these variables are downstream and treatment-selected, they are descriptive sensitivity analyses, not causal intervention evidence.

6. Methodological robustness：
   - log transform + PCA；
   - bootstrap；
   - complete-case；
   - Hb-free；
   - INR-free；
   - raw K-means sensitivity；
   - K=4 exploratory。

### 3.8 Limitations 必须包含

- Single database retrospective study。
- ICD-defined non-traumatic SAH，不等同完整影像确认的 aSAH。
- 缺少 Hunt-Hess、WFNS、modified Fisher、影像特征。
- 0-48h 生理变量可能受治疗影响。
- 过程性治疗和器官支持变量存在适应证混杂、下游中介、存活至治疗和时间顺序问题，不能作为干预因果效应解释。
- Cox/KM 仅评估住院期死亡时间，存活出院按出院删失，不能推断出院后长期生存。
- PCA 3 个 PC 解释方差有限，约 56%。
- K-means 依赖变量选择和预处理。
- RBC transfusion rate low，不能评估输血获益。
- 贫血与死亡可能有残余混杂。
- 需要外部验证。

### 3.9 审稿防守和语言风格

审稿人攻击点、正文内反击模板和高质量语言风格见：

`docs/high_impact_manuscript_standards.md`

生成稿必须按该标准预先处理以下本研究高风险问题：

- phenotype 是否只是 SOFA 复制品。
- 贫血变量进入聚类后再讨论贫血是否循环论证。
- INR/creatinine 极端值和偏态是否驱动聚类。
- K=2 或 K=4 是否比 K=3 更合理。
- 缺少影像、WFNS、Hunt-Hess、modified Fisher。
- 低 RBC 输血率导致不能指导输血策略。
- 过程性治疗模型不能指导 nimodipine、EVD/ICP、机械通气、血管活性药、CRRT 或 RBC 输注策略。
- 队列筛选流程是否缺少每一步人数；Figure 1 和 Methods 必须主动补足或说明 pipeline 未导出。
- ICD-based non-traumatic SAH 是否误分类；必须给出 ICD code/algorithm 或补充表占位，并在 Limitations 承认误分类风险。
- Methods 是否足够可复现；必须写清 PCA/K-means/logistic regression/cross-validation/bootstrap 的关键参数。
- Table 1 是否过薄；必须扩展 baseline/severity/process-of-care variables，避免只有少数变量。
- 最后的过程性治疗和住院期 survival 分析是否遗漏；必须在 Results 主文、Table 4 和 Supplementary Table 中呈现，而不是只留在 `analysis_result.md`。
- References 是否过少；必须补充 SAH、贫血、ICU phenotyping、unsupervised learning/reporting 相关文献。

## 4. 更新中文论文

同步更新 `dist/YYYYMMDD/manuscript_non_traumatic_sah_phenotypes_cn.md`。

要求：

- 与英文版内容一致；
- 学术中文表达；
- 不要机械翻译；
- 图表位置相同；
- 所有数字与英文版一致；
- 中文稿所有一级/二级标题、图表总标题和补充材料标题必须中文化；不要残留 `References`、`Tables`、`Supplementary Tables`、`Table 1` 等英文标题。建议使用“参考文献”“表格”“补充表”“表 1/图 1”。
- 中文稿参考文献可保留英文文献信息，但章节标题必须为“参考文献”，正文不要出现未解释的英文模板痕迹。
- phenotype 中文命名建议：
  - 表型 1：相对稳定低危型
  - 表型 2：神经损伤-循环应激型
  - 表型 3：多系统失衡高危型
- 不要在中文正文中只写裸 `P1/P2/P3`，首次出现需完整命名。

## 5. 生成 PDF

运行转换脚本：

```bash
DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH" python3 scripts/convert_manuscript_to_pdf.py YYYYMMDD
```

产出：

- `dist/YYYYMMDD/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf`
- `dist/YYYYMMDD/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf`

若 PDF 图表溢出、表格过宽或中文乱码，必须修复后重新生成。

## 6. 质量检查清单

生成完毕后逐项确认：

- [ ] `dist/YYYYMMDD/readme.txt` 已写入生成模型、日期和输入来源。
- [ ] 所有数据与 `dist/YYYYMMDD/analysis_result.md` 或 BigQuery 结果表一致。
- [ ] N 使用最新值，目前为 `1,186`，不是旧版 `1,187`。
- [ ] Figure 1 是 STROBE-style flow diagram，尽量包含每一步筛选人数；如结果表缺失筛选人数，已明确说明未编造并建议 pipeline 补充。
- [ ] Methods 或 Supplementary Table 5 列出 ICD code/队列算法、排除规则和 massive transfusion 定义；若当前结果缺失 code list，已明确标记而非编造。
- [ ] Methods 写清 PCA/K-means 参数、random seed/n_init、phenotype ordering、cross-validation、bootstrap resampling 和 logistic model covariates。
- [ ] 主方案写作是 `log1p(creatinine/INR) + PCA + K-means K=3`。
- [ ] raw standardized 8-variable K-means 只作为 sensitivity/reference。
- [ ] P1/P2/P3 的 n、死亡率、贫血率正确。
- [ ] K selection 同时解释 K=2 silhouette 更高、K=4 小簇问题，以及为什么 K=3 作为主方案。
- [ ] PCA 解释方差约 56.4%，没有写成 85% 或“大部分信息”。
- [ ] SOFA/SAPSII/OASIS/LODS 明确写作 external validation，不是聚类输入。
- [ ] 早期贫血定义明确：0-48h minimum Hb <10 g/dL。
- [ ] 没有声称贫血独立导致死亡。
- [ ] 没有声称某 phenotype 应接受输血。
- [ ] Results 主文包含过程性治疗和器官支持分布，不只是在 Table 1 或补充材料中出现。
- [ ] `phenotype_process_of_care_audit` 中的 nimodipine、EVD/ICP、vasopressor、mechanical ventilation、RBC transfusion、CRRT、fluid balance 数字已报告且与最新结果一致。
- [ ] `phenotype_process_of_care_adjusted_models` 中 specialty-care 和 organ-support 模型的 P2/P3 OR、95% CI 已写入正文或 Table 4，并明确不是 causal treatment effect。
- [ ] `phenotype_survival_logrank` 的 pairwise log-rank p 值已报告。
- [ ] `phenotype_survival_cox_models` 的 unadjusted、clinical adjusted、process-of-care adjusted Cox HR 已报告，并说明 alive discharges censored at hospital discharge。
- [ ] 没有把 nimodipine、EVD/ICP、vasopressor、mechanical ventilation、RBC、CRRT 或 fluid balance 的关联解释为干预获益/伤害。
- [ ] 调整后 OR、95% CI、p 值与结果表一致。
- [ ] Prediction AUROC/Brier 与结果表一致。
- [ ] Bootstrap ARI、complete-case、Hb-free、INR-free、no-RBC、ICU LOS >=48h、GCS alternatives 的数字一致。
- [ ] Table 1 包含 demographics、admission/evidence、aneurysm evidence、severity scores、process-of-care/organ support 和 outcomes；如果缺少变量，原因明确。
- [ ] References 不少于基础数据库/报告规范文献，已补充 SAH、贫血、ICU phenotyping 和 unsupervised learning 相关文献；没有伪造未核对文献。
- [ ] 中文稿标题完全中文化，没有残留 `References`、`Tables`、`Supplementary Tables`、`Table X` 等英文模板标题。
- [ ] 图表全部嵌入正文合适位置。
- [ ] 英文和中文版本结论一致。
- [ ] PDF 中图片清晰、表格不越界、中文不乱码。

```

---

## 辅助脚本说明

| 脚本                                     | 作用                             |
| ---------------------------------------- | -------------------------------- |
| `scripts/generate_manuscript_figures.py` | 根据分析结果数据生成论文 PNG 图 |
| `scripts/convert_manuscript_to_pdf.py`   | 将 Markdown 论文转为排版后的 PDF |

如果分析 pipeline 更新了主方案或结果表，必须同步更新这两个脚本中的硬编码数值和图表标题。
```
