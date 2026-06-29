-- 审稿人质疑专项质控：
-- 1. 为什么主分析只有 229 例？和预期 1500 例不一致在哪里发生？
-- 2. aSAH 定义是否准确？是否有 procedure code 验证？是否混入非动脉瘤性或创伤性 SAH？
--
-- 运行前提：
-- 已经运行 01_create_phenotype_cohort.sql，并生成 ash_study 下的中间表。
--
-- 输出表：
--   reviewer_qc_attrition_by_rule
--   reviewer_qc_asah_definition_levels
--   reviewer_qc_feature_availability_by_definition
--   reviewer_qc_procedure_code_audit
--   reviewer_qc_included_diagnosis_titles
--   reviewer_qc_possible_traumatic_or_nonaneurysmal

-- -----------------------------------------------------------------------------
-- 1. 逐条规则解释：229 是怎么来的
-- -----------------------------------------------------------------------------

-- 目的：把 cohort 损失拆成逐条筛选规则，而不只给最终 flowchart。
-- 原因：审稿人看到 1500 vs 229 时，会要求说明样本损失主要来自诊断严格化、ICU 条件还是变量完整度。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.reviewer_qc_attrition_by_rule` AS
WITH base AS (
    SELECT
        s.subject_id,
        s.hadm_id,
        s.is_adult,
        s.has_sah_dx,
        s.has_aneurysm_dx,
        s.has_aneurysm_procedure,
        s.has_traumatic_sah_dx,
        s.asah_evidence_level,
        f.stay_id,
        f.icu_los_hours,
        f.core_feature_missing_count,
        f.massive_transfusion_24h,
        f.eligible_primary_analysis,
        f.eligible_sensitivity_48h_los,
        f.eligible_no_transfusion_sensitivity
    FROM `mimic-study-498508.ash_study.source_sah_admissions` s
    LEFT JOIN `mimic-study-498508.ash_study.physiology_features_48h` f
        ON s.subject_id = f.subject_id
       AND s.hadm_id = f.hadm_id
)
SELECT
    '01_all_sah_icd_admissions' AS step,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients,
    NULL AS excluded_from_previous,
    'SAH ICD: ICD-9 430 or ICD-10 I60.x' AS rule
FROM base
UNION ALL
SELECT
    '02_adult_sah',
    COUNTIF(is_adult = 1),
    COUNT(DISTINCT IF(is_adult = 1, subject_id, NULL)),
    COUNTIF(is_adult != 1),
    'Age >=18'
FROM base
UNION ALL
SELECT
    '03_strict_asah_evidence_level_ge_2',
    COUNTIF(is_adult = 1 AND asah_evidence_level >= 2),
    COUNT(DISTINCT IF(is_adult = 1 AND asah_evidence_level >= 2, subject_id, NULL)),
    COUNTIF(is_adult = 1 AND asah_evidence_level < 2),
    'SAH plus aneurysm diagnosis or aneurysm procedure evidence'
FROM base
UNION ALL
SELECT
    '04_exclude_traumatic_sah_flag',
    COUNTIF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 0),
    COUNT(DISTINCT IF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 0, subject_id, NULL)),
    COUNTIF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 1),
    'Exclude explicit traumatic SAH flags'
FROM base
UNION ALL
SELECT
    '05_has_first_icu_stay',
    COUNTIF(stay_id IS NOT NULL),
    COUNT(DISTINCT IF(stay_id IS NOT NULL, subject_id, NULL)),
    COUNTIF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 0 AND stay_id IS NULL),
    'Has ICU stay and retained first ICU stay'
FROM base
UNION ALL
SELECT
    '06_icu_los_ge_24h',
    COUNTIF(stay_id IS NOT NULL AND icu_los_hours >= 24),
    COUNT(DISTINCT IF(stay_id IS NOT NULL AND icu_los_hours >= 24, subject_id, NULL)),
    COUNTIF(stay_id IS NOT NULL AND icu_los_hours < 24),
    'ICU length of stay >=24h'
FROM base
UNION ALL
SELECT
    '07_core_missing_le_2',
    COUNTIF(stay_id IS NOT NULL AND icu_los_hours >= 24 AND core_feature_missing_count <= 2),
    COUNT(DISTINCT IF(stay_id IS NOT NULL AND icu_los_hours >= 24 AND core_feature_missing_count <= 2, subject_id, NULL)),
    COUNTIF(stay_id IS NOT NULL AND icu_los_hours >= 24 AND core_feature_missing_count > 2),
    '8 core clustering features: <=2 missing'
FROM base
UNION ALL
SELECT
    '08_primary_analysis_no_massive_transfusion',
    COUNTIF(eligible_primary_analysis = 1),
    COUNT(DISTINCT IF(eligible_primary_analysis = 1, subject_id, NULL)),
    COUNTIF(stay_id IS NOT NULL AND icu_los_hours >= 24 AND core_feature_missing_count <= 2 AND massive_transfusion_24h = 1),
    'Primary cohort: no massive transfusion in first 24h'
FROM base
UNION ALL
SELECT
    '09_sensitivity_icu_los_ge_48h',
    COUNTIF(eligible_sensitivity_48h_los = 1),
    COUNT(DISTINCT IF(eligible_sensitivity_48h_los = 1, subject_id, NULL)),
    COUNTIF(eligible_primary_analysis = 1 AND icu_los_hours < 48),
    'Sensitivity cohort: ICU LOS >=48h'
FROM base
UNION ALL
SELECT
    '10_sensitivity_no_rbc_48h',
    COUNTIF(eligible_no_transfusion_sensitivity = 1),
    COUNT(DISTINCT IF(eligible_no_transfusion_sensitivity = 1, subject_id, NULL)),
    COUNTIF(eligible_primary_analysis = 1 AND eligible_no_transfusion_sensitivity = 0),
    'Sensitivity cohort: no RBC transfusion in first 48h'
FROM base;

SELECT *
FROM `mimic-study-498508.ash_study.reviewer_qc_attrition_by_rule`
ORDER BY step;

-- -----------------------------------------------------------------------------
-- 2. aSAH 定义分层：宽松、严格、procedure-confirmed 的样本差异
-- -----------------------------------------------------------------------------

-- 目的：比较不同 aSAH 定义下样本量、死亡率和主分析可用性。
-- 原因：这能回答“是否因为定义太严导致 229 例”的问题，也可支持主分析/敏感性分析选择。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.reviewer_qc_asah_definition_levels` AS
WITH source AS (
    SELECT
        s.subject_id,
        s.hadm_id,
        s.asah_evidence_level,
        s.has_aneurysm_dx,
        s.has_aneurysm_procedure,
        s.has_traumatic_sah_dx,
        s.is_adult,
        s.hospital_expire_flag,
        f.stay_id,
        f.eligible_primary_analysis,
        f.core_feature_missing_count,
        f.icu_los_hours
    FROM `mimic-study-498508.ash_study.source_sah_admissions` s
    LEFT JOIN `mimic-study-498508.ash_study.physiology_features_48h` f
        ON s.subject_id = f.subject_id
       AND s.hadm_id = f.hadm_id
)
SELECT
    'Level 1: SAH ICD only, adult, no trauma flag' AS definition,
    COUNTIF(is_adult = 1 AND has_traumatic_sah_dx = 0) AS admissions,
    COUNT(DISTINCT IF(is_adult = 1 AND has_traumatic_sah_dx = 0, subject_id, NULL)) AS patients,
    COUNTIF(is_adult = 1 AND has_traumatic_sah_dx = 0 AND stay_id IS NOT NULL) AS with_icu_feature_table,
    COUNTIF(is_adult = 1 AND has_traumatic_sah_dx = 0 AND eligible_primary_analysis = 1) AS primary_analysis_eligible,
    AVG(IF(is_adult = 1 AND has_traumatic_sah_dx = 0, CAST(hospital_expire_flag AS FLOAT64), NULL)) AS hospital_mortality
FROM source
UNION ALL
SELECT
    'Level 2: SAH ICD + aneurysm diagnosis/procedure, adult, no trauma flag',
    COUNTIF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 0),
    COUNT(DISTINCT IF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 0, subject_id, NULL)),
    COUNTIF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 0 AND stay_id IS NOT NULL),
    COUNTIF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 0 AND eligible_primary_analysis = 1),
    AVG(IF(is_adult = 1 AND asah_evidence_level >= 2 AND has_traumatic_sah_dx = 0, CAST(hospital_expire_flag AS FLOAT64), NULL))
FROM source
UNION ALL
SELECT
    'Level 3: SAH ICD + aneurysm procedure, adult, no trauma flag',
    COUNTIF(is_adult = 1 AND asah_evidence_level = 3 AND has_traumatic_sah_dx = 0),
    COUNT(DISTINCT IF(is_adult = 1 AND asah_evidence_level = 3 AND has_traumatic_sah_dx = 0, subject_id, NULL)),
    COUNTIF(is_adult = 1 AND asah_evidence_level = 3 AND has_traumatic_sah_dx = 0 AND stay_id IS NOT NULL),
    COUNTIF(is_adult = 1 AND asah_evidence_level = 3 AND has_traumatic_sah_dx = 0 AND eligible_primary_analysis = 1),
    AVG(IF(is_adult = 1 AND asah_evidence_level = 3 AND has_traumatic_sah_dx = 0, CAST(hospital_expire_flag AS FLOAT64), NULL))
FROM source;

SELECT *
FROM `mimic-study-498508.ash_study.reviewer_qc_asah_definition_levels`;

-- -----------------------------------------------------------------------------
-- 3. 不同 aSAH 定义下核心变量可用性
-- -----------------------------------------------------------------------------

-- 目的：检查样本减少是否主要由核心变量缺失造成。
-- 原因：如果 Level 1 有很多患者但变量完整度差，主分析 229 例是数据可用性限制，而非任意删样本。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.reviewer_qc_feature_availability_by_definition` AS
WITH labeled AS (
    SELECT
        CASE
            WHEN s.is_adult = 1 AND s.has_traumatic_sah_dx = 0 AND s.asah_evidence_level = 3 THEN 'Level 3 procedure-confirmed'
            WHEN s.is_adult = 1 AND s.has_traumatic_sah_dx = 0 AND s.asah_evidence_level >= 2 THEN 'Level 2 strict'
            WHEN s.is_adult = 1 AND s.has_traumatic_sah_dx = 0 THEN 'Level 1 broad'
            ELSE 'Excluded'
        END AS definition_level,
        f.*
    FROM `mimic-study-498508.ash_study.source_sah_admissions` s
    LEFT JOIN `mimic-study-498508.ash_study.physiology_features_48h` f
        ON s.subject_id = f.subject_id
       AND s.hadm_id = f.hadm_id
)
SELECT
    definition_level,
    COUNT(*) AS rows_count,
    COUNTIF(stay_id IS NOT NULL) AS has_feature_table_row,
    COUNTIF(core_feature_missing_count <= 2) AS core_missing_le_2,
    COUNTIF(eligible_primary_analysis = 1) AS primary_analysis_eligible,
    COUNTIF(hb_min_48h_all IS NOT NULL) AS hb_nonmissing,
    COUNTIF(gcs_motor_min_48h IS NOT NULL) AS gcs_nonmissing,
    COUNTIF(map_min_48h IS NOT NULL) AS map_nonmissing,
    COUNTIF(shock_index_max_48h IS NOT NULL) AS shock_index_nonmissing,
    COUNTIF(lactate_max_48h IS NOT NULL) AS lactate_nonmissing,
    COUNTIF(spo2_fio2_min_48h IS NOT NULL) AS spo2_fio2_nonmissing,
    COUNTIF(creatinine_max_48h IS NOT NULL) AS creatinine_nonmissing,
    COUNTIF(platelet_min_48h IS NOT NULL) AS platelet_nonmissing
FROM labeled
WHERE definition_level != 'Excluded'
GROUP BY definition_level
ORDER BY definition_level;

SELECT *
FROM `mimic-study-498508.ash_study.reviewer_qc_feature_availability_by_definition`
ORDER BY definition_level;

-- -----------------------------------------------------------------------------
-- 4. Procedure code 审计：当前命中的操作代码是否合理，是否漏掉候选代码
-- -----------------------------------------------------------------------------

-- 目的：列出所有被当前规则命中的 aneurysm procedure code 和 long title。
-- 原因：审稿人可能要求说明 clipping/coiling/endovascular 操作验证来自哪些 procedure code。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.reviewer_qc_procedure_code_audit` AS
SELECT
    pi.icd_version,
    pi.icd_code,
    dp.long_title,
    COUNT(*) AS procedure_rows,
    COUNT(DISTINCT pi.subject_id) AS patients,
    COUNT(DISTINCT pi.hadm_id) AS admissions,
    COUNTIF(s.has_sah_dx = 1) AS rows_with_sah_dx,
    COUNTIF(s.has_sah_dx = 1 AND s.has_traumatic_sah_dx = 0) AS rows_with_nontrauma_sah_dx
FROM `physionet-data.mimiciv_3_1_hosp.procedures_icd` pi
INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_procedures` dp
    ON pi.icd_code = dp.icd_code
   AND pi.icd_version = dp.icd_version
LEFT JOIN `mimic-study-498508.ash_study.dx_sah_flags` s
    ON pi.subject_id = s.subject_id
   AND pi.hadm_id = s.hadm_id
WHERE (
        LOWER(dp.long_title) LIKE '%aneurysm%'
    AND (
            LOWER(dp.long_title) LIKE '%clip%'
         OR LOWER(dp.long_title) LIKE '%coil%'
         OR LOWER(dp.long_title) LIKE '%embol%'
         OR LOWER(dp.long_title) LIKE '%repair%'
    )
)
OR (
        LOWER(dp.long_title) LIKE '%endovascular%'
    AND LOWER(dp.long_title) LIKE '%embol%'
)
GROUP BY pi.icd_version, pi.icd_code, dp.long_title
ORDER BY rows_with_nontrauma_sah_dx DESC, procedure_rows DESC;

SELECT *
FROM `mimic-study-498508.ash_study.reviewer_qc_procedure_code_audit`
ORDER BY rows_with_nontrauma_sah_dx DESC, procedure_rows DESC;

-- 目的：列出在 SAH 住院中可能相关、但未必被当前规则命中的 procedure title。
-- 原因：用于发现 clipping/coiling/embolization 映射是否漏检。
SELECT
    pi.icd_version,
    pi.icd_code,
    dp.long_title,
    COUNT(*) AS procedure_rows,
    COUNT(DISTINCT pi.hadm_id) AS admissions
FROM `physionet-data.mimiciv_3_1_hosp.procedures_icd` pi
INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_procedures` dp
    ON pi.icd_code = dp.icd_code
   AND pi.icd_version = dp.icd_version
INNER JOIN `mimic-study-498508.ash_study.source_sah_admissions` s
    ON pi.subject_id = s.subject_id
   AND pi.hadm_id = s.hadm_id
WHERE (
        LOWER(dp.long_title) LIKE '%clip%'
     OR LOWER(dp.long_title) LIKE '%coil%'
     OR LOWER(dp.long_title) LIKE '%embol%'
     OR LOWER(dp.long_title) LIKE '%aneurysm%'
     OR LOWER(dp.long_title) LIKE '%endovascular%'
)
GROUP BY pi.icd_version, pi.icd_code, dp.long_title
ORDER BY admissions DESC, procedure_rows DESC;

-- -----------------------------------------------------------------------------
-- 5. 纳入病例诊断标题审计：是否混入创伤性/非动脉瘤性 SAH
-- -----------------------------------------------------------------------------

-- 目的：列出主分析病例的所有 SAH/动脉瘤/创伤相关诊断标题。
-- 原因：用于人工检查是否混入 traumatic SAH、non-aneurysmal SAH 或其他非目标诊断。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.reviewer_qc_included_diagnosis_titles` AS
SELECT
    di.icd_version,
    di.icd_code,
    dd.long_title,
    COUNT(*) AS diagnosis_rows,
    COUNT(DISTINCT di.subject_id) AS patients,
    COUNT(DISTINCT di.hadm_id) AS admissions
FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
    ON di.icd_code = dd.icd_code
   AND di.icd_version = dd.icd_version
INNER JOIN `mimic-study-498508.ash_study.physiology_features_48h` f
    ON di.subject_id = f.subject_id
   AND di.hadm_id = f.hadm_id
WHERE f.eligible_primary_analysis = 1
  AND (
        LOWER(dd.long_title) LIKE '%subarachnoid%'
     OR LOWER(dd.long_title) LIKE '%aneurysm%'
     OR LOWER(dd.long_title) LIKE '%traumatic%'
     OR LOWER(dd.long_title) LIKE '%arteriovenous%'
     OR LOWER(dd.long_title) LIKE '%malformation%'
  )
GROUP BY di.icd_version, di.icd_code, dd.long_title
ORDER BY admissions DESC, diagnosis_rows DESC;

SELECT *
FROM `mimic-study-498508.ash_study.reviewer_qc_included_diagnosis_titles`
ORDER BY admissions DESC, diagnosis_rows DESC;

-- 目的：列出可能有创伤性或非动脉瘤性提示的主分析病例，供人工复核。
-- 原因：如果该表非空，需要逐例判断是否应排除或作为敏感性分析。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.reviewer_qc_possible_traumatic_or_nonaneurysmal` AS
SELECT DISTINCT
    f.subject_id,
    f.hadm_id,
    f.stay_id,
    di.icd_version,
    di.icd_code,
    dd.long_title
FROM `mimic-study-498508.ash_study.physiology_features_48h` f
INNER JOIN `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
    ON f.subject_id = di.subject_id
   AND f.hadm_id = di.hadm_id
INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
    ON di.icd_code = dd.icd_code
   AND di.icd_version = dd.icd_version
WHERE f.eligible_primary_analysis = 1
  AND (
        LOWER(dd.long_title) LIKE '%traumatic%'
     OR LOWER(dd.long_title) LIKE '%arteriovenous%'
     OR LOWER(dd.long_title) LIKE '%malformation%'
     OR LOWER(dd.long_title) LIKE '%nontraumatic subarachnoid hemorrhage, unspecified%'
     OR LOWER(dd.long_title) LIKE '%unspecified subarachnoid hemorrhage%'
  );

SELECT *
FROM `mimic-study-498508.ash_study.reviewer_qc_possible_traumatic_or_nonaneurysmal`
ORDER BY subject_id, hadm_id, icd_version, icd_code;

-- -----------------------------------------------------------------------------
-- 6. 建议用于 manuscript / response 的一行摘要
-- -----------------------------------------------------------------------------

SELECT
    (SELECT admissions FROM `mimic-study-498508.ash_study.reviewer_qc_attrition_by_rule` WHERE step = '01_all_sah_icd_admissions') AS broad_sah_admissions,
    (SELECT admissions FROM `mimic-study-498508.ash_study.reviewer_qc_attrition_by_rule` WHERE step = '03_strict_asah_evidence_level_ge_2') AS strict_asah_admissions,
    (SELECT admissions FROM `mimic-study-498508.ash_study.reviewer_qc_attrition_by_rule` WHERE step = '05_has_first_icu_stay') AS strict_asah_with_icu,
    (SELECT admissions FROM `mimic-study-498508.ash_study.reviewer_qc_attrition_by_rule` WHERE step = '07_core_missing_le_2') AS core_features_complete_enough,
    (SELECT admissions FROM `mimic-study-498508.ash_study.reviewer_qc_attrition_by_rule` WHERE step = '08_primary_analysis_no_massive_transfusion') AS primary_analysis_n,
    (SELECT COUNT(*) FROM `mimic-study-498508.ash_study.reviewer_qc_possible_traumatic_or_nonaneurysmal`) AS possible_trauma_or_nonaneurysmal_records_to_review;

