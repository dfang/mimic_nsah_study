-- 解释为什么文献为 750 patients，而当前查询 adult non-traumatic SAH ICD 为 720 patients
--
-- 重点核查：
-- 1. 当前 has_traumatic_sah_dx 是否把 "Nontraumatic subarachnoid hemorrhage" 误判为 traumatic。
-- 2. 修正 traumatic 规则后，adult non-traumatic SAH ICD 的人数是多少。
-- 3. 尽量模拟文献纳入规则：ICD-9 430 / ICD-10 I60，成人，首次 hospital/ICU，ICU LOS >=24h，Hb/Hct 不缺失。
--
-- 文献规则摘录：
-- MIMIC-IV v2.2；ICD-9 430 and ICD-10 I60；exclude ICU stays <24h,
-- age <18, non-first hospital and ICU admissions, missing hematocrit or hemoglobin.

-- -----------------------------------------------------------------------------
-- 1. 验证当前 traumatic flag 是否误伤 nontraumatic ICD title
-- -----------------------------------------------------------------------------

SELECT
    COUNT(*) AS source_sah_admissions,
    COUNTIF(has_traumatic_sah_dx = 1) AS current_traumatic_flagged,
    COUNTIF(
        has_traumatic_sah_dx = 1
        AND EXISTS (
            SELECT 1
            FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
            INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
                ON di.icd_code = dd.icd_code
               AND di.icd_version = dd.icd_version
            WHERE di.subject_id = s.subject_id
              AND di.hadm_id = s.hadm_id
              AND LOWER(dd.long_title) LIKE '%nontraumatic%subarachnoid%'
        )
    ) AS current_traumatic_flagged_with_nontraumatic_title
FROM `mimic-study-498508.asah_study.source_sah_admissions` s
WHERE is_adult = 1
  AND has_sah_dx = 1;

-- 查看被当前规则标记为 traumatic 的 SAH 诊断标题分布。
SELECT
    di.icd_version,
    di.icd_code,
    dd.long_title,
    COUNT(DISTINCT di.hadm_id) AS admissions
FROM `mimic-study-498508.asah_study.source_sah_admissions` s
INNER JOIN `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
    ON s.subject_id = di.subject_id
   AND s.hadm_id = di.hadm_id
INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
    ON di.icd_code = dd.icd_code
   AND di.icd_version = dd.icd_version
WHERE s.is_adult = 1
  AND s.has_sah_dx = 1
  AND s.has_traumatic_sah_dx = 1
  AND (
        (di.icd_version = 9 AND di.icd_code LIKE '430%')
     OR (di.icd_version = 10 AND di.icd_code LIKE 'I60%')
     OR LOWER(dd.long_title) LIKE '%subarachnoid%'
  )
GROUP BY di.icd_version, di.icd_code, dd.long_title
ORDER BY admissions DESC;

-- -----------------------------------------------------------------------------
-- 2. 使用修正后的 traumatic 规则重新统计 broad NSAH
-- -----------------------------------------------------------------------------

WITH corrected_flags AS (
    SELECT
        a.subject_id,
        a.hadm_id,
        p.anchor_age AS age,
        a.hospital_expire_flag,
        MAX(
            CASE
                WHEN di.icd_version = 9 AND di.icd_code LIKE '430%' THEN 1
                WHEN di.icd_version = 10 AND di.icd_code LIKE 'I60%' THEN 1
                ELSE 0
            END
        ) AS has_sah_dx,
        MAX(
            CASE
                WHEN di.icd_version = 10 AND di.icd_code LIKE 'S06.6%' THEN 1
                WHEN LOWER(dd.long_title) LIKE '%nontraumatic%subarachnoid%' THEN 0
                WHEN LOWER(dd.long_title) LIKE '%non-traumatic%subarachnoid%' THEN 0
                WHEN LOWER(dd.long_title) LIKE '%traumatic%subarachnoid%' THEN 1
                ELSE 0
            END
        ) AS corrected_traumatic_sah_dx
    FROM `physionet-data.mimiciv_3_1_hosp.admissions` a
    INNER JOIN `physionet-data.mimiciv_3_1_hosp.patients` p
        ON a.subject_id = p.subject_id
    INNER JOIN `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
        ON a.subject_id = di.subject_id
       AND a.hadm_id = di.hadm_id
    LEFT JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
        ON di.icd_code = dd.icd_code
       AND di.icd_version = dd.icd_version
    GROUP BY a.subject_id, a.hadm_id, p.anchor_age, a.hospital_expire_flag
)
SELECT
    'corrected_adult_nontraumatic_sah_icd' AS cohort_definition,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients,
    AVG(CAST(hospital_expire_flag AS FLOAT64)) AS hospital_mortality
FROM corrected_flags
WHERE age >= 18
  AND has_sah_dx = 1
  AND corrected_traumatic_sah_dx = 0;

-- -----------------------------------------------------------------------------
-- 3. 尽量模拟文献 flow：ICU、首次住院/首次 ICU、ICU >=24h、Hb/Hct 可用
-- -----------------------------------------------------------------------------

WITH corrected_sah AS (
    SELECT
        a.subject_id,
        a.hadm_id,
        a.admittime,
        a.dischtime,
        a.hospital_expire_flag,
        p.anchor_age AS age,
        MAX(
            CASE
                WHEN di.icd_version = 9 AND di.icd_code LIKE '430%' THEN 1
                WHEN di.icd_version = 10 AND di.icd_code LIKE 'I60%' THEN 1
                ELSE 0
            END
        ) AS has_sah_dx,
        MAX(
            CASE
                WHEN di.icd_version = 10 AND di.icd_code LIKE 'S06.6%' THEN 1
                WHEN LOWER(dd.long_title) LIKE '%nontraumatic%subarachnoid%' THEN 0
                WHEN LOWER(dd.long_title) LIKE '%non-traumatic%subarachnoid%' THEN 0
                WHEN LOWER(dd.long_title) LIKE '%traumatic%subarachnoid%' THEN 1
                ELSE 0
            END
        ) AS corrected_traumatic_sah_dx
    FROM `physionet-data.mimiciv_3_1_hosp.admissions` a
    INNER JOIN `physionet-data.mimiciv_3_1_hosp.patients` p
        ON a.subject_id = p.subject_id
    INNER JOIN `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
        ON a.subject_id = di.subject_id
       AND a.hadm_id = di.hadm_id
    LEFT JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
        ON di.icd_code = dd.icd_code
       AND di.icd_version = dd.icd_version
    GROUP BY a.subject_id, a.hadm_id, a.admittime, a.dischtime, a.hospital_expire_flag, p.anchor_age
),
first_hosp AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY subject_id ORDER BY admittime) AS hosp_seq
    FROM corrected_sah
    WHERE age >= 18
      AND has_sah_dx = 1
      AND corrected_traumatic_sah_dx = 0
),
icu_ranked AS (
    SELECT
        fh.subject_id,
        fh.hadm_id,
        ie.stay_id,
        fh.hospital_expire_flag,
        ie.intime AS icu_intime,
        ie.outtime AS icu_outtime,
        DATETIME_DIFF(ie.outtime, ie.intime, HOUR) AS icu_los_hours,
        ROW_NUMBER() OVER (
            PARTITION BY fh.subject_id, fh.hadm_id
            ORDER BY ie.intime
        ) AS icu_seq
    FROM first_hosp fh
    INNER JOIN `physionet-data.mimiciv_3_1_icu.icustays` ie
        ON fh.subject_id = ie.subject_id
       AND fh.hadm_id = ie.hadm_id
    WHERE fh.hosp_seq = 1
),
first_icu AS (
    SELECT *
    FROM icu_ranked
    WHERE icu_seq = 1
),
lab_availability AS (
    SELECT
        fi.subject_id,
        fi.hadm_id,
        fi.stay_id,
        MAX(CASE WHEN le.itemid = 51222 THEN 1 ELSE 0 END) AS has_hemoglobin,
        MAX(CASE WHEN le.itemid = 51221 THEN 1 ELSE 0 END) AS has_hematocrit
    FROM first_icu fi
    LEFT JOIN `physionet-data.mimiciv_3_1_hosp.labevents` le
        ON fi.subject_id = le.subject_id
       AND fi.hadm_id = le.hadm_id
       AND le.charttime >= fi.icu_intime
       AND le.charttime < DATETIME_ADD(fi.icu_intime, INTERVAL 24 HOUR)
       AND le.itemid IN (51221, 51222)
       AND le.valuenum IS NOT NULL
    GROUP BY fi.subject_id, fi.hadm_id, fi.stay_id
),
flow AS (
    SELECT
        '01_corrected_adult_nontraumatic_sah' AS step,
        COUNT(*) AS admissions,
        COUNT(DISTINCT subject_id) AS patients,
        NULL AS excluded_from_previous
    FROM first_hosp
    UNION ALL
    SELECT
        '02_first_hospital_admission',
        COUNTIF(hosp_seq = 1),
        COUNT(DISTINCT IF(hosp_seq = 1, subject_id, NULL)),
        COUNTIF(hosp_seq != 1)
    FROM first_hosp
    UNION ALL
    SELECT
        '03_has_icu_stay',
        COUNT(*),
        COUNT(DISTINCT subject_id),
        NULL
    FROM first_icu
    UNION ALL
    SELECT
        '04_first_icu_los_ge_24h',
        COUNTIF(icu_los_hours >= 24),
        COUNT(DISTINCT IF(icu_los_hours >= 24, subject_id, NULL)),
        COUNTIF(icu_los_hours < 24)
    FROM first_icu
    UNION ALL
    SELECT
        '05_hb_hct_available_in_first_24h',
        COUNTIF(fi.icu_los_hours >= 24 AND la.has_hemoglobin = 1 AND la.has_hematocrit = 1),
        COUNT(DISTINCT IF(fi.icu_los_hours >= 24 AND la.has_hemoglobin = 1 AND la.has_hematocrit = 1, fi.subject_id, NULL)),
        COUNTIF(fi.icu_los_hours >= 24 AND (COALESCE(la.has_hemoglobin, 0) = 0 OR COALESCE(la.has_hematocrit, 0) = 0))
    FROM first_icu fi
    LEFT JOIN lab_availability la
        ON fi.stay_id = la.stay_id
)
SELECT *
FROM flow
ORDER BY step;

