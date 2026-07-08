# 论文生成提示词

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
  - eICU 外部验证结果表：
    - `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
    - `eicu_external_phenotype_assignments`
    - `eicu_external_outcome_summary_by_phenotype`
    - `eicu_external_feature_summary_by_phenotype`
    - `eicu_external_assignment_quality`
    - `eicu_external_lightweight_tests`
    - `eicu_external_sensitivity_summary`
    - `eicu_external_severity_validation`
    - `eicu_de_novo_k3_summary`
    - `eicu_de_novo_k3_metrics`
    - `eicu_hb_free_anemia_regression`
    - `eicu_feature_missingness_summary`
    - `eicu_cohort_flowchart_counts`
    - `eicu_inr_missingness_audit`
- eICU 外部验证设计、结果和解释边界记录在 `docs/eicu_external_validation.md`。生成论文前必须阅读该文件，并以其中数字为准；若 BigQuery 表与文档冲突，以 BigQuery 最新表为准，并在 final report 中说明。

除非结果表已明确更新，不得编造数据。所有数字必须与最新 `analysis_result.md` 或 BigQuery 表一致。

## 0. 研究定位和写作边界

这篇论文的主定位是：

> 在 critically ill adults with non-traumatic SAH 中，利用 ICU 入科后 0-48 小时常规多模态生理数据识别早期临床可解释 phenotype，并评估其死亡风险、贫血负担和外部严重度一致性。

当前论文还必须纳入 eICU Collaborative Research Database 的外部验证：

> MIMIC-IV 为开发队列，eICU 为外部验证队列。主外部验证采用冻结 MIMIC 预处理、填补、标准化、PCA 和 K-means 质心的 Frozen Transport；eICU 原位 K=3 聚类只作为 structural sensitivity analysis。

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
- eICU 外部验证的结论边界：Frozen Transport 成功验证了风险分层的可转运性；eICU de novo clustering 只能说明存在类似风险梯度，不能说复现了相同患者级聚类边界，因为当前 ARI 接近 0。

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

图表总体要求：

- 重要数据结果应尽量可视化，不要只埋在正文或表格中。至少将 cohort flow、主 phenotype 生理中心、死亡/贫血/RBC 梯度、严重程度外部验证、预测性能、K 选择、bootstrap 稳定性、敏感性分析、PCA loadings、调整后 OR/HR、eICU 外部验证做成图或补充图。
- 图表应放在首次叙述对应结果的正文附近，而不是全部堆在文末：cohort flow 放在 Cohort/results 开头；phenotype heatmap 放在主 K=3 solution 后；outcomes/anemia 放在 outcome gradients 后；eICU 图放在 eICU external validation 小节；补充图放在 Supplementary Figures。
- 图表大小必须适合 A4 纵向 PDF：单栏/正文图建议宽 6.5-7.2 inch；横向多面板图建议宽 7.0-7.5 inch、高 3.5-4.8 inch；热图/森林图可略高但不超过 5.5 inch；补充多面板图如 4 个小面板应优先使用 2x2 或 1x4 但保证 PDF 中文字可读。
- 输出 PNG 建议 `dpi >= 300`，`bbox_inches="tight"`，并预留足够边距，避免坐标轴标签、图例、误差线文本或标题被裁切。
- 图内文字应专业、克制、可读：坐标轴标签完整，单位明确；标题简短；图例不遮挡数据；数值标签最多保留 1 位小数或 2-3 位有效数字；避免把大量原始表格数字塞进图内。
- 视觉风格应统一：P1/P2/P3 使用固定颜色；主图避免花哨渐变和过度装饰；热图使用发散色板并标明 z-score；森林图使用 log scale 和 OR/HR=1 参考线；柱状图显示百分比和样本量/事件数（空间允许时）。
- 色彩应兼顾色盲友好和打印效果；避免红绿对立作为唯一编码。背景保持白色，网格线淡化，字体统一。
- 如果某个关键结果尚无图，优先补充 `scripts/generate_manuscript_figures.py`，不要只在正文中描述。若受当前结果表限制暂不能作图，必须在 final report 中说明缺少哪张图和原因。
- 每次更新图表后必须重新生成 PDF 并检查图表是否完整显示、尺寸合理、文字清晰、没有溢出或被分页切断。

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
- `fig_s7_eicu_external_validation.png`：eICU Frozen Transport 外部验证。建议展示 eICU P1/P2/P3 的住院死亡率、ICU 死亡率、早期贫血率和 APACHE predicted mortality 梯度；若作图脚本暂不支持，正文和表格仍必须报告 eICU 结果。
- 如作图脚本支持，新增 `fig_s8_hospital_survival.png` 或同等图：按 phenotype 展示住院期 Kaplan-Meier/累积死亡曲线，并在图例或正文报告 pairwise log-rank。若脚本暂不支持，正文和表格仍必须报告 `phenotype_survival_logrank` / `phenotype_survival_cox_models` 的关键结果。

若脚本暂时只支持旧 8 图，请至少更新旧图中的数据和标题，确保主方案写成 log-PCA K=3，不再把 raw K-means 当主方案。

图表叙事和表格组织标准见 `docs/high_impact_manuscript_standards.md`。本研究至少应包含：

- Table 1：Baseline characteristics by phenotype。不得只列年龄、LOS、贫血、输血和死亡；应尽量包含 demographics、admission type、non-traumatic SAH evidence level、aneurysm diagnosis/procedure、SOFA/SAPS II/APS III/OASIS/LODS、mechanical ventilation、vasopressor、EVD/ICP、nimodipine、RBC transfusion、CRRT、hospital/ICU outcomes 等。若某变量未在当前结果表中出现，可省略但要优先从 `phenotype_baseline_characteristics` 和 process-of-care summary 中补齐。
- Table 2：Early physiological profiles by phenotype。
- Table 3：Outcome models。
- Table 4：Process-of-care and hospital-course models。必须汇总 `phenotype_process_of_care_adjusted_models` 与 `phenotype_survival_cox_models` 的核心 phenotype OR/HR，不得只写主 logistic 模型。Cox 表中 `cox_phenotype_process_of_care_exploratory` 必须标注 immortal time bias 风险和 exploratory sensitivity association。
- Table 5：eICU external validation。必须包含 eICU cohort flow、Frozen Transport P1/P2/P3 mortality/anemia/RBC、APACHE 外部效标、主要敏感性分析、de novo ARI/NMI/silhouette。若版面过长，可在正文放核心表，完整表放补充表。
- Supplementary Table 1：K selection and clustering diagnostics。
- Supplementary Table 2：Sensitivity analyses。
- Supplementary Table 3：Process-of-care distribution by phenotype。来自 `phenotype_process_of_care_audit`，至少包含 nimodipine、EVD/ICP、vasopressor、mechanical ventilation、RBC transfusion、CRRT、fluid balance。
- Supplementary Table 4：PCA loadings。
- Supplementary Table 5：Cohort definition / ICD code and exclusion algorithm。若当前结果没有 ICD code 明细，应在 Methods 明确代码定义位于 SQL/pipeline，并在补充表中写“code list to be supplied from cohort SQL”，不要伪造 ICD code。
- Supplementary Table 6：eICU feature mapping and missingness audit。必须包含 shock index HR/SBP 15 分钟配对规则、INR 缺失率和 INR missingness audit。

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

图表插入位置建议：

- Figure 1 紧跟 Cohort Selection / Cohort and feature availability 的首段。
- Figure 2 紧跟 Primary log-PCA K=3 solution 和 phenotype 命名段落。
- Figure 3 紧跟 Outcome gradients and anemia/process-of-care summary；如果同一图包含死亡、贫血和输血，应在图例中明确 RBC transfusion 是描述性过程变量。
- Figure 4 紧跟 external severity validation，且正文明确 SOFA/SAPSII/OASIS/LODS/APACHE 不进入聚类。
- Figure 5 紧跟 prediction performance 段落，并说明 phenotype 的价值是解释性压缩，不是替代完整连续变量预测模型。
- eICU 图紧跟 eICU external validation 小节，不要只放 Supplementary Figures。
- Supplementary Figures 应按首次引用顺序排列；每张补充图都要有足够图例，不能只写文件名或“see figure”。

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
- internal sensitivity analyses = raw K-means、complete-case、Hb-free、Hb-free anemia regression、INR-free、no-RBC、ICU LOS >=48h、GCS alternatives、K=4、process-of-care adjustment、hospital-course Cox/KM；
- external validation = eICU Frozen Transport using fixed MIMIC imputation, scaling, PCA, and phenotype centroids, with eICU de novo clustering as structural sensitivity。

Results：

- N 必须使用最新结果，目前为 `1,186`；
- hospital deaths 目前为 `235`，overall mortality `19.8%`；
- P1/P2/P3 当前主 log-PCA 结果：
  - P1: n=694, hospital mortality 6.3%, early anemia 12.1%
  - P2: n=384, hospital mortality 32.6%, early anemia 41.4%
  - P3: n=108, hospital mortality 61.1%, early anemia 66.7%
- log-PCA K=3 silhouette 约 0.334；
- raw K-means K=3 silhouette 约 0.224；
- log-PCA bootstrap mean/median ARI 约 0.919/0.926；
- phenotype adjusted OR 显著；
- early anemia adjusted OR 不显著；
- SOFA/SAPSII/OASIS/LODS 随 phenotype 递增。
- process-of-care adjusted logistic models attenuate but do not remove phenotype mortality associations；
- hospital-course log-rank and Cox models show persistent phenotype gradients；必须明确 alive discharges censored at hospital discharge。
- eICU Frozen Transport external validation:
  - eICU validation N = 843；
  - P1/P2/P3 hospital mortality = 5.4%、25.7%、42.7%；
  - APACHE score 和 predicted mortality 随 transported phenotype 单调升高；
  - eICU transport sensitivities preserve the monotonic mortality gradient；
  - eICU de novo clustering recovers a risk gradient but has low agreement with frozen labels, ARI approximately -0.003。

Conclusions：

- 早期多模态生理 phenotype 能识别不同死亡风险层级；
- P3 是多系统失衡高危表型；
- 贫血富集于高危 phenotype，但更像系统性失衡标志，而非独立因果因素。
- 不得把 “RBC transfusion OR/HR 不显著” 写成“输血无效”或“输血没有获益”；当前研究没有因果识别设计，只能说不能评价输血获益、无效或最佳 Hb 阈值。

### 3.4 Introduction 写作要点

三段式：

1. non-traumatic SAH ICU 患者死亡风险高，异质性大，预后不仅取决于神经损伤，也受循环、氧合、肾功能、凝血、贫血影响。
2. 传统 GCS/WFNS/SOFA 有用，但不能表达 ICU 早期多系统生理组合；早期贫血在 SAH 中常见，但其是否为独立危险因素或高危状态标志不清楚。
3. 本研究目标：

- 识别 early multimodal physiological phenotypes；
- 比较 mortality 和 severity score；
- 探索 early anemia 在 phenotype 中的分布和预后意义；
- 在 eICU 中进行外部验证，评估 MIMIC-derived phenotypes 的可转运性和结构稳健性。

### 3.5 Methods 写作要点

必须写清楚：

**Data source**

- MIMIC-IV 3.1；
- eICU Collaborative Research Database for external validation；
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

**eICU external validation cohort**

必须新增 Methods 小节，标题建议为 “External validation in eICU”。

写清楚：

- 数据源：eICU Collaborative Research Database through BigQuery；
- adult first ICU stays with non-traumatic SAH evidence；
- SAH evidence from eICU diagnosis text, ICD-9 code 430, or `apacheadmissiondx`；
- trauma/head injury/traumatic SAH text excluded；
- ICU LOS >=24h；
- primary eligibility = eight core features with <=2 missing；
- eICU 不把 massive transfusion 作为主排除，因为 transfusion 记录单位在 `infusiondrug` 和 `intakeoutput` 中不统一；记录 RBC exposure 用于描述和 sensitivity；
- strict-SAH sensitivity 要求 diagnosis ICD/text evidence，而不是 admissionDx-only；
- ICU LOS >=48h、no recorded RBC、low-missing、complete-case、INR-free transport 作为 eICU 外部验证敏感性分析。

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

**Frozen transport external validation**

必须写清楚 eICU 主外部验证不是重新聚类，而是：

- 在 MIMIC 开发队列中固定 median imputer；
- 固定 creatinine/INR `log1p` 处理；
- 固定 MIMIC StandardScaler mean/std；
- 固定 MIMIC PCA eigenvectors；
- 固定 MIMIC K=3 phenotype centroids in 3-PC space；
- 将 eICU 患者投影到同一空间；
- 按最近 MIMIC centroid 分配 P1/P2/P3；
- 报告 nearest-centroid distance、assignment margin、低 margin 比例；
- eICU de novo log-PCA K=3 只用于 structural sensitivity，并用 ARI/NMI/same ordered label rate/silhouette 与 frozen labels 比较。

写作边界：

- Frozen Transport 是主外部验证，因为它模拟新中心/新患者应用固定分类器；
- de novo eICU clustering 不能作为主外部验证，因为它在验证集上重新拟合了分布和边界；
- de novo ARI 接近 0 时，必须写“risk gradient reproduced, exact patient-level boundaries not reproduced”，不得写“clusters replicated”。

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
- eICU external validation statistical analyses：必须说明 Frozen Transport、transported phenotype outcome summaries、APACHE external criterion validation、transport sensitivity analyses、de novo ARI/NMI/silhouette、Hb-free anemia regression。

Methods 中还必须明确：

- 聚类是 unsupervised；hospital mortality、SOFA、SAPSII、OASIS、LODS、RBC transfusion 均未作为聚类输入。
- 过程性治疗和器官支持变量也未作为聚类输入；它们只用于 Table 1/补充表描述、过程性治疗敏感性模型和住院期 time-to-event 补充分析。
- phenotype 命名是在聚类完成后基于标准化中心和原始中位数解释，不是先验人工规则。
- K=3 不是单纯按 silhouette 最大选择；选择理由是临床可解释性、最小簇样本量、风险梯度、bootstrap 稳定性和敏感性分析综合判断。
- K=2 代表粗略低/高风险二分，K=4 代表高分辨率探索但小簇较小；二者均不作为主方案。
- 任何 SOFA-adjusted 模型如果未被 pipeline 正式写入结果表，必须标记为 exploratory post hoc，不得作为主验证结论。
- MIMIC 中的 SOFA/SAPSII/OASIS/LODS 是 internal external-severity validation；eICU 中的 APACHE score/predicted mortality 是 external-database criterion validation。二者要区分，不能混写成同一个数据源。
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
     - nimodipine 48h：overall 675/1186 (56.9%)；P1 434/694 (62.5%)；P2 224/384 (58.3%)；P3 17/108 (15.7%)。
     - EVD/ICP 48h：overall 322/1186 (27.2%)；P1 121/694 (17.4%)；P2 186/384 (48.4%)；P3 15/108 (13.9%)。
     - vasopressor 48h：overall 252/1186 (21.2%)；P1 43/694 (6.2%)；P2 154/384 (40.1%)；P3 55/108 (50.9%)。
     - mechanical ventilation 48h：overall 431/1186 (36.3%)；P1 122/694 (17.6%)；P2 247/384 (64.3%)；P3 62/108 (57.4%)。
     - RBC transfusion 48h：overall 24/1186 (2.0%)；P1 3/694 (0.4%)；P2 13/384 (3.4%)；P3 8/108 (7.4%)。
     - CRRT 48h：overall 10/1186 (0.8%)；P1 0/694 (0.0%)；P2 1/384 (0.3%)；P3 9/108 (8.3%)。
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

8. eICU external validation
   - 这一节必须写入正文，不得只放补充材料。
   - 先明确：MIMIC-derived frozen classifier was transported to eICU without refitting preprocessing, PCA, or centroids。
   - eICU cohort flow 必须报告：
     - SAH candidate unit stays 2,880；patients 2,571；
     - adult 2,863/2,554；
     - non-traumatic 1,314/1,158；
     - first ICU stay 1,153；
     - ICU LOS >=24h 903；
     - primary validation eligible 843；
     - ICU LOS >=48h sensitivity 626；
     - no recorded RBC sensitivity 819；
     - strict SAH sensitivity 605；
     - <=1 missing sensitivity 819；
     - complete-case sensitivity 428。
   - eICU feature missingness 必须报告：
     - INR missing 446/903 (49.4%)；
     - platelet missing 75/903 (8.3%)；
     - Hb missing 64/903 (7.1%)；
     - creatinine missing 31/903 (3.4%)；
     - shock index/MAP/SpO2 missing each 10/903 (1.1%)；
     - GCS motor missing 5/903 (0.6%)。
   - 必须说明 shock index extraction was improved by matching HR to nearest periodic/aperiodic SBP within 15 minutes；893 patients had matched HR/SBP pairs，median matched pairs 440，mean median pairing gap 2.83 minutes。
   - Frozen Transport 结果必须报告：
     - eICU N=843；
     - P1 n=539, hospital mortality 5.4%, ICU mortality 2.8%, early anemia 11.4%, RBC 0-48h 0.4%；
     - P2 n=222, hospital mortality 25.7%, ICU mortality 16.2%, early anemia 34.5%, RBC 0-48h 5.9%；
     - P3 n=82, hospital mortality 42.7%, ICU mortality 29.3%, early anemia 58.0%, RBC 0-48h 11.0%。
   - eICU physiological profiles 必须简要报告：
     - P1: Hb 11.9, GCS motor 6, MAP 62.0, shock index 0.88, SpO2 90.0, creatinine 0.75, INR 1.1, platelet 207.0；
     - P2: Hb 10.7, GCS motor 4, MAP 51.0, shock index 1.14, SpO2 92.0, creatinine 0.81, INR 1.1, platelet 202.5；
     - P3: Hb 9.5, GCS motor 4, MAP 51.5, shock index 1.26, SpO2 74.5, creatinine 1.54, INR 1.5, platelet 146.0。
   - Assignment quality 必须报告：
     - median nearest-centroid distance 1.337；
     - median assignment margin 1.050；
     - low margin <0.10 = 4.4%；
     - low margin <0.25 = 12.0%。
   - eICU APACHE external criterion validation 必须报告：
     - acute physiology score median P1/P2/P3 = 27/49/67, Spearman rho 0.508, p=2.29e-51；
     - APACHE score median P1/P2/P3 = 36/57/79, rho 0.480, p=3.58e-45；
     - predicted hospital mortality median P1/P2/P3 = 0.069/0.243/0.426, rho 0.445, p=2.00e-38；
     - predicted ICU mortality median P1/P2/P3 = 0.039/0.175/0.299, rho 0.453, p=6.15e-40。
   - eICU transport sensitivities 必须报告方向：
     - primary frozen transport mortality P1/P2/P3 = 5.4%/25.7%/42.7%；
     - ICU LOS >=48h = 6.9%/24.2%/33.9%；
     - no recorded RBC = 5.4%/25.8%/39.7%；
     - strict SAH = 6.6%/30.5%/45.6%；
     - <=1 missing = 5.4%/25.9%/40.5%；
     - complete case = 7.2%/33.6%/43.1%；
     - INR-free transport = 4.6%/24.4%/38.7%。
   - INR missingness audit 必须解释：
     - INR measured patients were sicker: mortality 19.0%, APACHE mean 52.7, predicted hospital mortality 21.7%；
     - INR missing patients: mortality 9.0%, APACHE mean 43.1, predicted hospital mortality 13.1%；
     - 因此 INR 缺失不是 MCAR，INR-free transport 必须作为重要敏感性分析。
   - eICU de novo clustering 必须报告但降级解释：
     - de novo P1/P2/P3 mortality = 5.8%/18.1%/42.0%；
     - ARI -0.003，NMI 0.002，same ordered label rate 43.9%，silhouette 0.269；
     - 结论只能是 “risk gradient emerged de novo, but exact frozen patient-level boundaries did not replicate”。
   - eICU Hb-free anemia sensitivity 必须报告：
     - P2 vs P1 OR 6.16 (95% CI 3.74-10.13), p=8.30e-13；
     - P3 vs P1 OR 10.27 (95% CI 5.68-18.57), p=1.22e-14；
     - early anemia OR 1.47 (95% CI 0.92-2.36), p=0.105。

9. Internal sensitivity analyses
   - raw K-means 方向一致；
   - complete-case 方向一致；
   - Hb-free 方向一致，反驳 Hb 循环论证；
   - INR-free 不改善 silhouette，支持保留 INR；
   - no-RBC 和 ICU LOS >=48h 方向一致；
   - GCS alternatives 改变 assignment，说明神经变量选择重要，GCS motor 需说明是预设且低缺失；
   - K=4 作为探索性高分辨率分型。
   - 敏感性分析的总结必须围绕“是否支持主结论”而不是逐项报流水账。

### 3.7 Discussion 必须包含的论点

按 7 段组织：

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

6. eICU external validation：
   - eICU Frozen Transport is the main external validation and supports transportability of the MIMIC-derived risk-stratifying phenotype classifier；
   - eICU APACHE score and predicted mortality gradients provide external criterion validation；
   - eICU transport sensitivities show robustness to LOS >=48h, no recorded RBC, strict SAH definition, missingness restrictions, complete case, and INR-free transport；
   - eICU de novo clustering produced a mortality gradient but did not reproduce exact frozen patient-level labels；this argues for transportable risk structure rather than discrete universally identical subtype boundaries；
   - INR missingness in eICU is informative and must be acknowledged.

7. Methodological robustness：
   - log transform + PCA；
   - bootstrap；
   - complete-case；
   - Hb-free；
   - INR-free；
   - raw K-means sensitivity；
   - K=4 exploratory。

8. Future directions / next analyses：
   - 不要只写泛泛“future work”。必须明确提出下一阶段分析路线：
     - 从 0-48h 极值扩展到生理轨迹，使用纵向特征摘要、functional data analysis、latent class mixed models，或 LSTM/Transformer 等序列模型捕捉趋势、波动和恢复速度。
     - 分析动态表型转化，例如入 ICU 24h 表型、72h 表型，以及 P1 向 P3-like physiology 转化的恶化轨迹。
     - 将动态窗口延伸到 SAH 后第 4-10 天 delayed cerebral ischemia (DCI) 高风险期；如果当前数据/脚本未生成这些结果，只能写为 future analysis，不得编造结果。
     - 比较 Gaussian Mixture Model/LPA、HDBSCAN、Deep Embedded Clustering 和 semi-supervised phenotyping；必须说明这些是后续方法学扩展，除非结果表已经生成，否则不要把它们写成已完成分析。
     - 对 RBC transfusion 若要讨论疗效，后续必须使用 target trial emulation、propensity-score matching/weighting、instrumental-variable analysis（仅在有可信工具变量时）或 time-varying treatment model 来处理 confounding by indication 和 immortal-time bias。

### 3.8 Limitations 必须包含

- Retrospective database study；虽然已加入 eICU 外部验证，仍缺少前瞻性、影像确认和多国队列验证。
- ICD-defined non-traumatic SAH，不等同完整影像确认的 aSAH。
- 缺少 Hunt-Hess、WFNS、modified Fisher、影像特征。
- 0-48h 生理变量可能受治疗影响。
- 过程性治疗和器官支持变量存在适应证混杂、下游中介、存活至治疗和时间顺序问题，不能作为干预因果效应解释。
- Cox/KM 仅评估住院期死亡时间，存活出院按出院删失，不能推断出院后长期生存。
- PCA 3 个 PC 解释方差有限，约 56%。
- K-means 依赖变量选择和预处理。
- RBC transfusion rate low，不能评估输血获益。
- 当前输血分析仅为描述/敏感性关联；不能得出“输血无效”“输血有害”或“某 Hb 阈值最佳”的因果结论。若要研究输血效应，必须作为后续因果推断研究单独设计。
- 贫血与死亡可能有残余混杂。
- 当前主表型定义使用 0-48h 极值，未捕捉完整生理轨迹的形状、斜率、波动性、恢复速度和 24-72h 转化；可能遗漏 DCI 高峰期（约 SAH 后 4-10 天）相关的动态恶化信号。
- eICU 外部验证依赖 diagnosis text、ICD-9 430 和 admissionDx，仍可能存在 SAH 误分类。
- eICU INR 缺失率高且具有 informative missingness；INR-free sensitivity 缓解但不能完全消除该问题。
- eICU de novo clustering 与 frozen labels 的 ARI 接近 0，说明不同数据库中的患者级边界并不稳定；论文应表述为 transportable risk-stratifying phenotypes，而不是固定生物亚型实体。
- 仍需要影像确认、临床分级齐全的外部队列进一步验证。

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
- eICU 外部验证是否遗漏；必须在 Abstract、Methods、Results、Discussion、Limitations、Table 5 或 Supplementary Table 中呈现。
- eICU Frozen Transport 和 eICU de novo clustering 是否被混淆；必须明确 Frozen Transport 是主外部验证，de novo 只是 structural sensitivity。
- eICU de novo ARI 接近 0 是否被过度包装；不得写成“replicated clusters”，只能写成“replicated risk gradient but not patient-level boundaries”。
- eICU INR 缺失是否被忽略；必须报告 49.4% missing、informative missingness audit 和 INR-free sensitivity。
- References 是否过少；必须补充 SAH、贫血、ICU phenotyping、unsupervised learning/reporting 相关文献。
- 后续分析建议是否被具体写出：动态轨迹表型、LSTM/Transformer 或 functional data analysis、GMM/HDBSCAN/Deep Embedded Clustering/semi-supervised phenotyping、以及输血因果推断设计。
- 摘要和正文中的极小 p 值应统一写作 `p < 0.001`，不要保留 `7.07e-23` 这类科学计数法；表格中也优先用 `<0.001` 节省版面。
- PDF 生成后必须检查是否存在图表裁切、连续数字乱码或文本提取异常，例如 `0.37 0.37 0.37...`；若出现，先修复 Markdown/PDF 转换脚本或表格布局，再重新生成 PDF。

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
- [ ] 关键结果已尽量可视化：主 phenotype 中心、死亡/贫血/RBC 梯度、严重程度验证、预测性能、K 选择、bootstrap、敏感性分析、eICU 外部验证和 OR/HR forest plot 均有主图或补充图；若缺图，final report 已说明原因。
- [ ] 每张图插入在首次叙述对应结果附近；eICU 外部验证图不只放在补充材料。
- [ ] 图表尺寸适合 A4 PDF：没有过大、过小、跨页截断或边缘裁切；多面板图中文字仍可读。
- [ ] 图表视觉风格统一且专业：P1/P2/P3 颜色一致，字体/标题/图例/坐标轴单位清楚，数值标签不过密，色彩兼顾打印和色盲友好。
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
- [ ] 没有把 RBC transfusion 不显著写成输血无效/无益；若提到输血疗效，只能写为后续需要因果推断设计。
- [ ] Results 主文包含过程性治疗和器官支持分布，不只是在 Table 1 或补充材料中出现。
- [ ] `phenotype_process_of_care_audit` 中的 nimodipine、EVD/ICP、vasopressor、mechanical ventilation、RBC transfusion、CRRT、fluid balance 数字已报告且与最新结果一致。
- [ ] `phenotype_process_of_care_adjusted_models` 中 specialty-care 和 organ-support 模型的 P2/P3 OR、95% CI 已写入正文或 Table 4，并明确不是 causal treatment effect。
- [ ] `phenotype_survival_logrank` 的 pairwise log-rank p 值已报告。
- [ ] `phenotype_survival_cox_models` 的 unadjusted、clinical adjusted、process-of-care adjusted Cox HR 已报告，并说明 alive discharges censored at hospital discharge。
- [ ] 没有把 nimodipine、EVD/ICP、vasopressor、mechanical ventilation、RBC、CRRT 或 fluid balance 的关联解释为干预获益/伤害。
- [ ] eICU 外部验证已进入 Abstract、Methods、Results、Discussion、Limitations，而不是只放在补充材料。
- [ ] eICU 主验证写成 Frozen Transport：固定 MIMIC median imputer、log transform、StandardScaler、PCA eigenvectors 和 K=3 centroids 后投影到 eICU。
- [ ] eICU 结果使用最新值：N=843；P1/P2/P3 hospital mortality = 5.4%/25.7%/42.7%；ICU mortality = 2.8%/16.2%/29.3%；early anemia = 11.4%/34.5%/58.0%。
- [ ] eICU APACHE 外部效标已报告：APACHE score median 36/57/79；predicted hospital mortality median 0.069/0.243/0.426。
- [ ] eICU 敏感性分析已报告：LOS >=48h、no recorded RBC、strict SAH、<=1 missing、complete case、INR-free transport 均保留单调死亡率梯度。
- [ ] eICU de novo clustering 明确作为 structural sensitivity，且写清 ARI 约 -0.003、NMI 0.002、silhouette 0.269；没有写成 exact cluster replication。
- [ ] eICU INR 缺失已报告：446/903 (49.4%)，并说明 INR measured patients were sicker；INR-free transport 被保留为重要敏感性分析。
- [ ] eICU shock index 提取逻辑已写明：HR 与 15 分钟内最近 periodic/aperiodic SBP 配对；shock index missing 10/903 (1.1%)。
- [ ] eICU Hb-free anemia sensitivity 已报告：phenotype OR 显著，early anemia OR 1.47 (95% CI 0.92-2.36), p=0.105。
- [ ] Limitations 不再写“需要外部验证”作为主要空缺；应写“已有 eICU 外部验证，但仍需前瞻性、影像确认和临床分级完整队列验证”。
- [ ] 调整后 OR、95% CI、p 值与结果表一致。
- [ ] Prediction AUROC/Brier 与结果表一致。
- [ ] Bootstrap ARI、complete-case、Hb-free、INR-free、no-RBC、ICU LOS >=48h、GCS alternatives 的数字一致。
- [ ] Table 1 包含 demographics、admission/evidence、aneurysm evidence、severity scores、process-of-care/organ support 和 outcomes；如果缺少变量，原因明确。
- [ ] References 不少于基础数据库/报告规范文献，已补充 SAH、贫血、ICU phenotyping 和 unsupervised learning 相关文献；没有伪造未核对文献。
- [ ] Discussion 或 Future Directions 明确写入动态轨迹表型、24h/72h 转化、DCI 4-10 天窗口、高级聚类/半监督表型和输血因果推断后续路线，并清楚标记为未来分析而非当前结果。
- [ ] 摘要、正文和表格中的极小 p 值统一为 `p < 0.001` 或 `<0.001`，没有科学计数法 p 值。
- [ ] 中文稿标题完全中文化，没有残留 `References`、`Tables`、`Supplementary Tables`、`Table X` 等英文模板标题。
- [ ] 图表全部嵌入正文合适位置。
- [ ] 英文和中文版本结论一致。
- [ ] PDF 中图片清晰、表格不越界、中文不乱码。
- [ ] PDF 文本抽查没有连续数字乱码或图表残缺；尤其检查包含 Figure 2、Figure 3、Table 3/4 和 Supplementary Figures 的页面。
- [ ] PDF 视觉抽查至少覆盖：第一个主图页、一个横向多面板图页、一个热图页、一个宽表页、一个补充图页；确认图表完整、美观、可读。

```

---

## 辅助脚本说明

| 脚本                                     | 作用                             |
| ---------------------------------------- | -------------------------------- |
| `scripts/generate_manuscript_figures.py` | 根据分析结果数据生成论文 PNG 图 |
| `scripts/convert_manuscript_to_pdf.py`   | 将 Markdown 论文转为排版后的 PDF |

如果分析 pipeline 更新了主方案或结果表，必须同步更新这两个脚本中的硬编码数值和图表标题。
```
