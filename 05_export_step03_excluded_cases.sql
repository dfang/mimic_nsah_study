-- 导出第 3 步被排除的病例：
-- 03_strict_asah_evidence_level_ge_2 排除规则：
--   成人 SAH ICD 住院中，未满足“SAH + 动脉瘤诊断或动脉瘤操作证据”的病例。
--
-- 目的：
-- 1. 列出被排除的 1317 条住院记录。
-- 2. 给每条记录标记为什么未达到 strict aSAH evidence level >=2。
-- 3. 汇总这些病例的 SAH ICD 标题、创伤/AVM/未特指诊断提示和相关 procedure 候选。

-- -----------------------------------------------------------------------------
-- 1. 逐病例导出：第 3 步被排除的 adult SAH records
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.step03_excluded_cases` AS
WITH sah_dx_titles AS (
    SELECT
        di.subject_id,
        di.hadm_id,
        STRING_AGG(
            DISTINCT CONCAT(CAST(di.icd_version AS STRING), ':', di.icd_code, ' | ', dd.long_title),
            ' ;; '
            ORDER BY CONCAT(CAST(di.icd_version AS STRING), ':', di.icd_code, ' | ', dd.long_title)
        ) AS sah_diagnosis_titles
    FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
    INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
        ON di.icd_code = dd.icd_code
       AND di.icd_version = dd.icd_version
    WHERE (
            (di.icd_version = 9 AND di.icd_code LIKE '430%')
         OR (di.icd_version = 10 AND di.icd_code LIKE 'I60%')
         OR LOWER(dd.long_title) LIKE '%subarachnoid%'
    )
    GROUP BY di.subject_id, di.hadm_id
),
aneurysm_dx_titles AS (
    SELECT
        di.subject_id,
        di.hadm_id,
        STRING_AGG(
            DISTINCT CONCAT(CAST(di.icd_version AS STRING), ':', di.icd_code, ' | ', dd.long_title),
            ' ;; '
            ORDER BY CONCAT(CAST(di.icd_version AS STRING), ':', di.icd_code, ' | ', dd.long_title)
        ) AS aneurysm_diagnosis_titles
    FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
    INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
        ON di.icd_code = dd.icd_code
       AND di.icd_version = dd.icd_version
    WHERE (
            (di.icd_version = 9 AND di.icd_code = '437.3')
         OR (di.icd_version = 10 AND di.icd_code LIKE 'I67.1%')
         OR LOWER(dd.long_title) LIKE '%aneurysm%'
    )
    GROUP BY di.subject_id, di.hadm_id
),
possible_nonasah_dx AS (
    SELECT
        di.subject_id,
        di.hadm_id,
        MAX(CASE WHEN di.icd_version = 10 AND di.icd_code LIKE 'S06.6%' THEN 1 ELSE 0 END) AS has_s066_traumatic_sah_code,
        MAX(CASE WHEN LOWER(dd.long_title) LIKE '%traumatic%' THEN 1 ELSE 0 END) AS has_traumatic_title,
        MAX(
            CASE
                WHEN LOWER(dd.long_title) LIKE '%arteriovenous malformation%' THEN 1
                WHEN LOWER(dd.long_title) LIKE '%vascular malformation%' THEN 1
                WHEN LOWER(dd.long_title) LIKE '%avm%' THEN 1
                ELSE 0
            END
        ) AS has_avm_or_malformation_title,
        MAX(
            CASE
                WHEN LOWER(dd.long_title) LIKE '%unspecified subarachnoid%' THEN 1
                WHEN LOWER(dd.long_title) LIKE '%subarachnoid hemorrhage, unspecified%' THEN 1
                WHEN LOWER(dd.long_title) LIKE '%subarachnoid haemorrhage, unspecified%' THEN 1
                ELSE 0
            END
        ) AS has_unspecified_sah_title,
        STRING_AGG(
            DISTINCT CASE
                WHEN LOWER(dd.long_title) LIKE '%traumatic%'
                  OR LOWER(dd.long_title) LIKE '%arteriovenous malformation%'
                  OR LOWER(dd.long_title) LIKE '%vascular malformation%'
                  OR LOWER(dd.long_title) LIKE '%avm%'
                  OR LOWER(dd.long_title) LIKE '%unspecified subarachnoid%'
                  OR LOWER(dd.long_title) LIKE '%subarachnoid hemorrhage, unspecified%'
                  OR LOWER(dd.long_title) LIKE '%subarachnoid haemorrhage, unspecified%'
                THEN CONCAT(CAST(di.icd_version AS STRING), ':', di.icd_code, ' | ', dd.long_title)
                ELSE NULL
            END,
            ' ;; '
            ORDER BY CASE
                WHEN LOWER(dd.long_title) LIKE '%traumatic%'
                  OR LOWER(dd.long_title) LIKE '%arteriovenous malformation%'
                  OR LOWER(dd.long_title) LIKE '%vascular malformation%'
                  OR LOWER(dd.long_title) LIKE '%avm%'
                  OR LOWER(dd.long_title) LIKE '%unspecified subarachnoid%'
                  OR LOWER(dd.long_title) LIKE '%subarachnoid hemorrhage, unspecified%'
                  OR LOWER(dd.long_title) LIKE '%subarachnoid haemorrhage, unspecified%'
                THEN CONCAT(CAST(di.icd_version AS STRING), ':', di.icd_code, ' | ', dd.long_title)
                ELSE NULL
            END
        ) AS possible_nonasah_diagnosis_titles
    FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
    INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
        ON di.icd_code = dd.icd_code
       AND di.icd_version = dd.icd_version
    GROUP BY di.subject_id, di.hadm_id
),
all_relevant_procedures AS (
    SELECT
        pi.subject_id,
        pi.hadm_id,
        STRING_AGG(
            DISTINCT CONCAT(CAST(pi.icd_version AS STRING), ':', pi.icd_code, ' | ', dp.long_title),
            ' ;; '
            ORDER BY CONCAT(CAST(pi.icd_version AS STRING), ':', pi.icd_code, ' | ', dp.long_title)
        ) AS possible_aneurysm_or_neuro_procedure_titles,
        MAX(
            CASE
                WHEN LOWER(dp.long_title) LIKE '%aneurysm%' THEN 1
                WHEN LOWER(dp.long_title) LIKE '%clip%' THEN 1
                WHEN LOWER(dp.long_title) LIKE '%coil%' THEN 1
                WHEN LOWER(dp.long_title) LIKE '%embol%' THEN 1
                WHEN LOWER(dp.long_title) LIKE '%endovascular%' THEN 1
                WHEN LOWER(dp.long_title) LIKE '%craniotomy%' THEN 1
                ELSE 0
            END
        ) AS has_possible_neurovascular_procedure_title
    FROM `physionet-data.mimiciv_3_1_hosp.procedures_icd` pi
    INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_procedures` dp
        ON pi.icd_code = dp.icd_code
       AND pi.icd_version = dp.icd_version
    WHERE LOWER(dp.long_title) LIKE '%aneurysm%'
       OR LOWER(dp.long_title) LIKE '%clip%'
       OR LOWER(dp.long_title) LIKE '%coil%'
       OR LOWER(dp.long_title) LIKE '%embol%'
       OR LOWER(dp.long_title) LIKE '%endovascular%'
       OR LOWER(dp.long_title) LIKE '%craniotomy%'
       OR LOWER(dp.long_title) LIKE '%cerebral%'
       OR LOWER(dp.long_title) LIKE '%intracranial%'
    GROUP BY pi.subject_id, pi.hadm_id
)
SELECT
    s.subject_id,
    s.hadm_id,
    s.admittime,
    s.dischtime,
    s.age,
    s.gender,
    s.race,
    s.admission_type,
    s.insurance,
    s.hospital_expire_flag,
    s.has_sah_dx,
    s.has_aneurysm_dx,
    s.has_aneurysm_procedure,
    s.has_traumatic_sah_dx,
    s.asah_evidence_level,
    CASE
        WHEN s.is_adult != 1 THEN 'not_adult'
        WHEN s.has_sah_dx = 1 AND s.has_aneurysm_dx = 0 AND s.has_aneurysm_procedure = 0 THEN 'excluded_at_step03_no_aneurysm_dx_or_procedure_evidence'
        ELSE 'other'
    END AS step03_exclusion_reason,
    COALESCE(nonasah.has_s066_traumatic_sah_code, 0) AS has_s066_traumatic_sah_code,
    COALESCE(nonasah.has_traumatic_title, 0) AS has_traumatic_title,
    COALESCE(nonasah.has_avm_or_malformation_title, 0) AS has_avm_or_malformation_title,
    COALESCE(nonasah.has_unspecified_sah_title, 0) AS has_unspecified_sah_title,
    COALESCE(proc.has_possible_neurovascular_procedure_title, 0) AS has_possible_neurovascular_procedure_title,
    sah.sah_diagnosis_titles,
    aneurysm.aneurysm_diagnosis_titles,
    nonasah.possible_nonasah_diagnosis_titles,
    proc.possible_aneurysm_or_neuro_procedure_titles
FROM `mimic-study-498508.ash_study.source_sah_admissions` s
LEFT JOIN sah_dx_titles sah
    ON s.subject_id = sah.subject_id
   AND s.hadm_id = sah.hadm_id
LEFT JOIN aneurysm_dx_titles aneurysm
    ON s.subject_id = aneurysm.subject_id
   AND s.hadm_id = aneurysm.hadm_id
LEFT JOIN possible_nonasah_dx nonasah
    ON s.subject_id = nonasah.subject_id
   AND s.hadm_id = nonasah.hadm_id
LEFT JOIN all_relevant_procedures proc
    ON s.subject_id = proc.subject_id
   AND s.hadm_id = proc.hadm_id
WHERE s.is_adult = 1
  AND s.has_sah_dx = 1
  AND s.asah_evidence_level < 2;

-- 查看被排除病例总数。应接近 flowchart 第 3 步 excluded_from_previous = 1317。
SELECT
    COUNT(*) AS excluded_rows,
    COUNT(DISTINCT subject_id) AS excluded_patients,
    COUNT(DISTINCT hadm_id) AS excluded_admissions
FROM `mimic-study-498508.ash_study.step03_excluded_cases`;

-- -----------------------------------------------------------------------------
-- 2. 排除原因汇总
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.step03_excluded_reason_summary` AS
SELECT
    step03_exclusion_reason,
    has_traumatic_title,
    has_avm_or_malformation_title,
    has_unspecified_sah_title,
    has_possible_neurovascular_procedure_title,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients,
    COUNTIF(hospital_expire_flag = 1) AS deaths,
    AVG(CAST(hospital_expire_flag AS FLOAT64)) AS hospital_mortality
FROM `mimic-study-498508.ash_study.step03_excluded_cases`
GROUP BY
    step03_exclusion_reason,
    has_traumatic_title,
    has_avm_or_malformation_title,
    has_unspecified_sah_title,
    has_possible_neurovascular_procedure_title
ORDER BY admissions DESC;

SELECT *
FROM `mimic-study-498508.ash_study.step03_excluded_reason_summary`
ORDER BY admissions DESC;

-- -----------------------------------------------------------------------------
-- 3. 被排除病例的 SAH ICD 标题分布
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.step03_excluded_sah_code_summary` AS
SELECT
    di.icd_version,
    di.icd_code,
    dd.long_title,
    COUNT(*) AS diagnosis_rows,
    COUNT(DISTINCT di.subject_id) AS patients,
    COUNT(DISTINCT di.hadm_id) AS admissions
FROM `mimic-study-498508.ash_study.step03_excluded_cases` e
INNER JOIN `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
    ON e.subject_id = di.subject_id
   AND e.hadm_id = di.hadm_id
INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
    ON di.icd_code = dd.icd_code
   AND di.icd_version = dd.icd_version
WHERE (di.icd_version = 9 AND di.icd_code LIKE '430%')
   OR (di.icd_version = 10 AND di.icd_code LIKE 'I60%')
   OR LOWER(dd.long_title) LIKE '%subarachnoid%'
GROUP BY di.icd_version, di.icd_code, dd.long_title
ORDER BY admissions DESC, diagnosis_rows DESC;

SELECT *
FROM `mimic-study-498508.ash_study.step03_excluded_sah_code_summary`
ORDER BY admissions DESC, diagnosis_rows DESC;

-- -----------------------------------------------------------------------------
-- 4. 可能被误排除的病例：无 aneurysm dx/procedure，但有具体 I60.0-I60.7 非创伤 SAH
-- -----------------------------------------------------------------------------

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.step03_excluded_probable_asah_candidates` AS
SELECT *
FROM `mimic-study-498508.ash_study.step03_excluded_cases`
WHERE has_traumatic_title = 0
  AND has_s066_traumatic_sah_code = 0
  AND has_avm_or_malformation_title = 0
  AND (
        REGEXP_CONTAINS(sah_diagnosis_titles, r'I60\\.[0-7]')
     OR REGEXP_CONTAINS(sah_diagnosis_titles, r'9:430')
  );

SELECT
    COUNT(*) AS probable_asah_candidates,
    COUNT(DISTINCT subject_id) AS patients,
    COUNTIF(hospital_expire_flag = 1) AS deaths,
    AVG(CAST(hospital_expire_flag AS FLOAT64)) AS hospital_mortality
FROM `mimic-study-498508.ash_study.step03_excluded_probable_asah_candidates`;

SELECT *
FROM `mimic-study-498508.ash_study.step03_excluded_probable_asah_candidates`
ORDER BY subject_id, hadm_id
LIMIT 100;

