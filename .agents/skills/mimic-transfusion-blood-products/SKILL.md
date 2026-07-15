---
name: mimic-transfusion-blood-products
description: Work with anemia, hemoglobin, red blood cell transfusion, and blood product exposure in MIMIC-IV. Use for RBC transfusion definitions, blood product itemid/code searches, hemoglobin windows, pre/post-index exposure separation, ICU inputevents, EMAR triangulation, and transfusion-related confounding checks.
---

# MIMIC Transfusion And Blood Products

用这个 skill 处理 MIMIC-IV 中的 anemia、hemoglobin、RBC transfusion 和 blood products。输血暴露很容易受时间窗、适应证混杂和数据源不完整影响，必须显式定义。

读取患者级输血/用药记录前先应用 `mimic-data-governance`。通用暴露、结局和 adjudication 产物遵循 `mimic-exposure-outcome-builder`；本 skill 只补充输血领域定义。

## 先定义临床问题

- 暴露是 any RBC transfusion、单位数、剂量、时间到首次输血，还是血红蛋白阈值触发？
- 分别定义 cohort entry、index、treatment assignment、exposure end 和 follow-up start；不要用一个 `T0` 混用这些时间。
- 输血窗口是 baseline、early treatment、还是 follow-up treatment？
- 结局窗口是否在输血暴露之后，避免 immortal time bias？

## 数据源优先级

- ICU 给入量：`icu.inputevents`，用于 ICU 内血制品 administration evidence。
- 医院给药记录：`hosp.emar`、`hosp.emar_detail`，用于 medication administration context。
- 医嘱/药房：`hosp.prescriptions`、`hosp.pharmacy`，用于 order context，不等同于实际给入。
- 实验室：`derived.complete_blood_count` 或 `hosp.labevents`，用于 hemoglobin、hematocrit、platelet 等。

不要假设单一表完整覆盖输血。高风险研究应 triangulate 多个来源，并报告定义。

## RBC 暴露定义

常见变量：

- `rbc_any_0_48h`
- `rbc_units_0_48h`
- `rbc_first_time_0_48h`
- `rbc_time_from_index_hours`
- `pre_assignment_rbc_any`
- `hemoglobin_min_before_rbc`

区分：

- RBC / packed red blood cells。
- platelets。
- plasma / FFP。
- cryoprecipitate。
- albumin 或非血制品容量扩容，不能混入 blood products。

## Anemia 与 Lab 窗口

- hemoglobin 优先从 `derived.complete_blood_count` 抽取。
- 明确 pre-treatment hemoglobin：不能把输血后的 hemoglobin 当作 baseline confounder。
- 对 ICU 入科附近 labs，明确相对哪个命名时间使用 lookback，例如 assignment 前 `-6h to 0h`。
- 输出 min/first/last/count/missing flags。

## 混杂与偏倚

- RBC transfusion 常是疾病严重程度和出血严重度的 marker。
- baseline confounders 必须在治疗前测量。
- 不要把 post-treatment hemoglobin、vasopressor escalation、post-treatment shock 作为 baseline 调整变量。
- 如做因果分析，明确 positivity、confounding by indication、immortal time bias。

## 审查清单

- 暴露窗口是否相对命名清楚的 index/assignment time 明确？
- order 与 administration 是否区分？
- RBC 与其他 blood products 是否区分？
- pre-treatment hemoglobin 是否真的发生在输血前？
- 是否保留 item labels 或 matched evidence 供审计？
