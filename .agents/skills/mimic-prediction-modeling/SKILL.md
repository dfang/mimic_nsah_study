---
name: mimic-prediction-modeling
description: Develop, audit, internally validate, evaluate, freeze, and document clinical prediction models using MIMIC-IV. Use for diagnostic or prognostic models that require a subject-level split, explicit prediction landmark and horizon, leakage-safe preprocessing, bootstrap or nested cross-validation, calibration, discrimination, clinical utility, subgroup fairness evaluation, model freezing, or a model card. Do not use to estimate treatment effects or to name unsupervised phenotypes.
---

# MIMIC Prediction Modeling

Build prediction models whose performance corresponds to a real decision point and can be reproduced on new patients. Prefer a well-validated simple baseline over unsupported algorithm complexity.

Apply `mimic-data-governance` before reading features or training models. Treat split membership, embeddings, serialized models, and model weights derived from MIMIC as sensitive unless release review establishes otherwise.

## 选择操作

- `operation: build`：开发、验证、冻结并记录模型。
- `operation: audit`：只读审查现有 specification、pipeline、split、results 和 model card；不得训练、调参、重校准、生成新结果表或更新模型。

audit 由 `mimic-review` 调用时，使用同一 `review_run_id` 与 `input_hashes`，按 `../mimic-review/assets/templates/review-pass-receipt.yaml` 返回 `pass_id: prediction`、`coverage_status`、`recommendation`、canonical findings 和 `gate_effect`；缺少可核验材料时标记 `not-assessed`。

audit 分开报告三个轴，不能用一个总分掩盖问题：

1. **development quality**：样本、landmark、患者级拆分、fold 内预处理、模型选择、过拟合和冻结证据；
2. **evaluation risk of bias**：独立性、调参污染、reference standard/outcome、缺失、指标、校准、不确定性与完整 pipeline 的 internal validation；
3. **intended-use applicability**：目标人群、setting、时点、预测 horizon、可用 predictors、行动与临床效用。

使用 PROBAST+AI 的适用 domain 评价偏倚风险与适用性；TRIPOD+AI 只评价报告完整性，不能替代方法学有效性判断。

## Required prediction contract

Define before accessing model performance:

- prediction subtype: `diagnostic` or `prognostic`;
- target population and deployment setting;
- one prediction unit and its relationship to `subject_id`;
- eligibility time, prediction landmark or decision time, and prediction horizon;
- outcome definition and the risk set at the landmark;
- predictor availability cutoff and intended users or action;
- baseline comparator and candidate model families;
- internal validation, tuning, missing-data, and fairness plans.

For diagnostic prediction, also define the target condition, reference standard, target ascertainment window, reference-standard availability, blinding, and indeterminate-result handling. Predictors must not contain the reference standard or information created from it. For prognostic time-to-event prediction, define censoring, competing events, the target estimand, and horizon-specific evaluation.

If using measurements from ICU hours `0-24`, set the landmark at or after hour 24 and specify how death, discharge, or other events before that landmark affect eligibility. Do not call ICU admission the prediction time while using future measurements.

## Workflow

1. **Validate the prediction table.** Check one row per prediction instance, patient linkage, landmark eligibility, outcome prevalence, follow-up sufficiency, missingness, duplicates, and predictor timestamps.
2. **Partition by patient.** Keep every row for one `subject_id` in one partition across training, tuning, calibration, and evaluation. For temporal or site validation, preserve the intended chronology or site boundary as well.
3. **Define a locked evaluation design.** Read [references/validation-and-evaluation.md](references/validation-and-evaluation.md). Use bootstrap optimism correction for model development when appropriate, or nested cross-validation when tuning and algorithm comparison require it. Reserve any final evaluation set from all selection decisions.
4. **Build a complete pipeline.** Fit imputation, encoding, scaling, feature selection, and tuning only within each training or resampling fold. Keep a clinically meaningful baseline comparator.
5. **Evaluate beyond discrimination.** Separate discrimination (for example AUROC, AUPRC, or C-index), calibration, overall probabilistic scores such as Brier or log score, continuous point-prediction errors when applicable, and clinical utility. Use censoring- and competing-risk-aware evaluation for time-to-event outcomes.
6. **Assess subgroup performance and fairness.** Examine clinically and sociodemographically important groups with denominators, event counts, intervals, calibration, and intended-use context. Do not equate one parity metric with clinical fairness.
7. **Freeze the model.** After internal performance estimation, refit the locked pipeline on the complete development set when appropriate, without using evaluation data. Freeze feature definitions, timing, preprocessing objects, feature order, coefficients or serialized estimator, software versions, and assignment code before external validation. Freeze thresholds only when the intended use requires an action/classification decision and never select them on evaluation data.
8. **Document the model.** Copy [assets/model-card-template.md](assets/model-card-template.md). Link every metric and plot to reproducible code and a frozen evaluation artifact.

## Hard gates

- Never split repeated admissions or stays from the same patient across partitions.
- Never tune hyperparameters, thresholds, feature selection, or calibration on the final evaluation data.
- Never allow predictors measured after the landmark or variables that encode the outcome or future care.
- Never perform imputation or scaling on the full dataset before resampling.
- Never report only AUROC; include calibration, uncertainty, prevalence-sensitive performance, and clinical utility where decisions are claimed.
- Never claim transportability from internal validation. Use `mimic-external-validation` after freezing.
- Never describe a model as clinically useful solely because it is statistically accurate.

## Completion criteria

Finish only when the temporal contract is coherent, patient grouping is preserved, preprocessing is leakage-safe, tuning and evaluation are separated, a baseline comparison exists, uncertainty/calibration/utility/fairness are reported, and the frozen model plus completed model card can reproduce predictions.
