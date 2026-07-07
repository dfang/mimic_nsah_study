# 高分医学论文写作标准

本文档用于指导临床研究论文生成，尤其适用于回顾性队列、ICU 数据库、无监督学习、风险分层和表型识别研究。生成 manuscript 前应先阅读并遵循本标准；具体研究的样本量、变量、结果和结论边界以项目 prompt 和最新结果表为准。

## 1. 总体原则

高分论文必须按“临床问题驱动 + 方法透明 + 结论克制 + 审稿可防守”的标准写，而不是简单罗列模型输出。

核心要求：

- Introduction 必须提出明确临床空白，而不是泛泛说“机器学习有用”。
- Methods 必须可复现，清楚写出 cohort、时间窗、变量聚合、预处理、模型选择、敏感性分析。
- Results 必须围绕主问题组织，不要按代码输出顺序堆表。
- Discussion 必须解释临床含义、与传统评分/既有文献的关系、机制解释边界和方法稳健性。
- Limitations 必须主动承认设计和数据限制，不要等审稿人指出。
- 所有算法术语必须服务临床解释，避免写成纯 AI/ML 炫技论文。
- 所有结论都要有对应数字支撑；没有结果表支持的句子必须删除或写成 future work。

推荐文章定位：

> clinically interpretable risk stratification, physiological phenotyping, and hypothesis-generating clinical epidemiology study

避免定位为：

> causal effect study, treatment recommendation study, treatment response discovery, or black-box AI prediction study

## 2. 核心故事线

全文应形成一条清晰临床叙事：

1. 临床人群存在重要异质性，传统单一评分或单一实验室指标不能充分描述。
2. 早期常规临床数据可以识别临床可解释的风险层级或 phenotype。
3. 这些 phenotype 应有明确的生理含义、风险梯度和外部临床一致性。
4. 关键暴露或特征可以是 phenotype 的组成标志，但除非有因果设计，不能写成因果驱动因素。
5. 敏感性分析用于证明结果不是算法幻觉、变量选择偶然性或缺失值处理造成。

## 3. Abstract 标准

摘要应高度压缩，避免方法细节堆砌。

必须包含：

- **Background**：临床问题和知识空白。
- **Methods**：数据源、队列、时间窗、核心变量、主要算法、主要结局、关键敏感性分析。
- **Results**：样本量、事件数、主要 phenotype/分组、主要风险梯度、关键模型效应、关键稳健性结果。
- **Conclusions**：只写结果支持的结论，避免因果和治疗建议过度。

摘要中不要使用夸张词：

- “proved”
- “caused”
- “AI-powered”
- “precision treatment”
- “treatment-responsive subgroup”

除非研究确实有前瞻性验证或因果设计。

## 4. Introduction 标准

建议三段式：

1. **临床背景**：疾病负担、预后异质性、现有评估方式的不足。
2. **知识空白**：现有研究缺少什么，为什么已有评分/单变量分析不能回答。
3. **研究目标**：用 2-3 个明确目标描述本研究，不要把探索性目标写成验证性目标。

Introduction 的最后一句应清楚写：

> We aimed to identify clinically interpretable early physiological phenotypes and evaluate their associations with outcomes and clinically relevant features.

## 5. Methods 标准

Methods 是高分论文的核心。必须做到别人能复现。

### 5.1 Data Source

写清：

- 数据库名称和版本。
- 数据访问方式。
- 伦理/去标识化说明。
- 研究设计为 retrospective cohort。

### 5.2 Cohort Definition

必须写清：

- 纳入标准。
- 排除标准。
- index time / T0。
- 只保留首次事件或首次 ICU stay 的理由。
- 如果使用 ICD，应说明代码定义和误分类风险。
- 如果某些高特异性证据不作为纳入标准，应说明它们用于分层、协变量或敏感性。

### 5.3 Time Window

写清：

- baseline window。
- exposure/feature window。
- outcome window。
- 为什么选择该窗口。
- 该窗口是否可能受治疗影响。

### 5.4 Feature Selection

写清每个变量：

- 生理维度。
- 聚合方式，例如 minimum、maximum、first、mean。
- 单位和临床合理范围。
- 缺失率。
- 为什么纳入。
- 为什么未纳入高缺失或选择性检测变量。

变量选择必须体现“预先指定”和“临床合理”，不要写成根据结果挑变量。

### 5.5 Model / Clustering

无监督学习研究必须写清：

- 缺失值处理。
- 分布变换。
- 标准化方式。
- 降维方法和解释方差。
- 聚类算法和随机种子。
- K 值选择依据。
- cluster 命名规则。
- bootstrap 或其他稳定性评估。

K 值选择不能只看单一指标。应综合：

- silhouette / Davies-Bouldin / Calinski-Harabasz。
- 最小簇样本量。
- 临床解释性。
- outcome gradient。
- bootstrap 稳定性。
- 敏感性分析。

### 5.6 Outcomes and Regression

写清：

- 主要结局。
- 次要结局。
- 协变量选择依据。
- 是否做 interaction。
- 如果事件数有限，必须避免过度建模。

### 5.7 Sensitivity Analyses

敏感性分析应围绕可预期审稿问题设计，例如：

- 原始模型 vs 变换模型。
- complete-case vs imputation。
- 删除关键变量。
- 替代变量定义。
- 替代时间窗。
- 替代 K 值。
- 排除治疗影响明显的患者。
- 外部严重度评分验证。

## 6. Results 标准

Results 应按临床故事组织，不按脚本输出顺序。

推荐顺序：

1. Cohort selection and baseline event rate。
2. Feature availability and data quality。
3. Primary model / phenotype solution。
4. Clinical interpretation of phenotypes。
5. Outcome gradient。
6. Key exposure/feature distribution across phenotypes。
7. External clinical validation。
8. Regression and prediction analyses。
9. Sensitivity analyses。

Results 写法要求：

- 每段第一句说明该段要回答的问题。
- 正文只报关键数字，完整数字放表。
- 不要过度强调 p 值，优先报告效应量和临床梯度。
- 不要把敏感性分析写成流水账，需总结其是否支持主结论。

## 7. Discussion 标准

Discussion 建议 5 段。

### 7.1 Principal Findings

第一段必须直接总结 3-4 个主要发现。

### 7.2 Clinical Interpretation

解释 phenotype 或风险层级的临床样子。避免只说“Cluster 1/2/3”。

### 7.3 Relationship With Existing Scores or Literature

说明与传统评分、既往研究、临床认知的关系。

如果传统评分未作为模型输入，却与结果梯度一致，可以写成 external validation。

如果调整传统评分后仍有信号，可以写成 exploratory evidence that the phenotype captures information beyond global severity alone。但必须克制。

### 7.4 Mechanistic Interpretation

解释机制时使用谨慎措辞：

- “may reflect”
- “may represent”
- “is consistent with”
- “suggests”

除非有因果设计，不能写：

- “caused”
- “mediated”
- “drives”
- “treatment-responsive”

### 7.5 Robustness and Clinical Implications

说明敏感性分析如何支持主结论，以及对临床评估有何启发。

临床意义应写成：

- better characterization
- risk stratification
- hypothesis generation
- future prospective validation

不要直接写成治疗推荐。

## 8. Limitations 标准

必须主动写出：

- 单中心/单数据库/回顾性。
- 误分类风险。
- 缺少关键临床变量或影像变量。
- 时间窗内变量可能受治疗影响。
- 缺失值和选择性检测。
- 模型依赖变量选择和预处理。
- 事件数限制。
- 无外部验证。
- 不能推断因果或治疗效果。

Limitations 不应过短。高分论文通常宁愿主动承认限制，也不要显得回避。

## 9. Tables 标准

### Table 1. Baseline Characteristics

包括：

- Overall + groups/phenotypes。
- demographics。
- admission characteristics。
- etiology/evidence level if relevant。
- severity scores。
- primary and secondary outcomes。
- p value。

### Table 2. Clinical or Physiological Profiles

包括：

- 核心模型变量。
- 原始单位 median [IQR]。
- 关键临床特征。
- p value。

### Table 3. Outcome Models

包括：

- main-effect model。
- interaction model if prespecified。
- severity-score adjusted model if relevant。
- OR/HR、95% CI、p value。

### Supplementary Tables

包括：

- feature missingness。
- K selection/model diagnostics。
- PCA/loadings if applicable。
- bootstrap stability。
- sensitivity analyses。
- alternative definitions。

表格应可读，不要把几十列塞入主文。过宽表格放 supplement。

## 10. Figures 标准

每张图必须回答一个问题。

推荐结构：

- Figure 1：cohort flowchart。
- Figure 2：primary model / phenotype heatmap。
- Figure 3：outcome gradient。
- Figure 4：external validation。
- Figure 5：prediction or regression summary。
- Supplementary figures：K selection、bootstrap、sensitivity、alternative K、loadings。

Figure legend 必须包含：

- cohort。
- sample size。
- plotted measure。
- abbreviations。
- interpretation note if needed。

## 11. 常见审稿攻击点与反击模板

### 攻击点 1：只是复制传统严重度评分

反击：

- 传统评分未进入模型。
- 传统评分梯度作为 external validation。
- 若调整传统评分后结果仍存在，可报告为 exploratory supportive evidence。
- 不要声称完全独立于严重度。

### 攻击点 2：关键变量进入模型后又讨论该变量，存在循环论证

反击：

- 做 key-variable-free sensitivity。
- 说明该变量是 phenotype 组成特征，不是独立因果结论。
- 避免把该变量写成模型外独立发现。

### 攻击点 3：极端值或偏态变量驱动结果

反击：

- 预先做 log/Box-Cox 等分布变换。
- 标准化。
- PCA 或稳健敏感性。
- complete-case / outlier sensitivity。

### 攻击点 4：K 值选择任意

反击：

- 报告多种 K 指标。
- 说明 K=2 过粗、K=4 小簇或解释性不足。
- 用 bootstrap、最小簇大小和临床解释支持主 K。

### 攻击点 5：不能指导治疗

反击：

- 主动承认 observational and hypothesis-generating。
- 不做治疗效应结论。
- 将治疗反应写为 future prospective or causal study。

## 12. 高质量语言风格

英文使用医学期刊风格，避免营销式表达。

推荐词：

- “identified”
- “was associated with”
- “was enriched in”
- “may represent”
- “is consistent with”
- “supports clinical interpretability”
- “hypothesis-generating”

慎用或避免：

- “proved”
- “caused”
- “drives”
- “AI-powered”
- “precision treatment”
- “treatment-responsive”
- “clinically actionable” unless prospectively validated

正文中不要堆 p 值。优先报告：

- effect size。
- absolute risk。
- median [IQR]。
- confidence interval。
- clinical gradient。

Discussion 每段第一句要有明确 topic sentence。Conclusion 应短，通常不超过 120-150 英文词。
