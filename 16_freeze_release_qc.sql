-- Aggregate-only release QC for the non-traumatic SAH phenotype study.
-- This script must run only after the governance gate confirms an authorized user.

CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.freeze_release_qc_summary` AS
WITH base AS (
    SELECT *
    FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
),
repeated AS (
    SELECT subject_id
    FROM base
    GROUP BY subject_id
    HAVING COUNT(DISTINCT hadm_id) > 1
),
metrics AS (
    SELECT 'all_feature_rows' AS metric, COUNT(*) AS metric_value FROM base
    UNION ALL
    SELECT 'distinct_subjects', COUNT(DISTINCT subject_id) FROM base
    UNION ALL
    SELECT 'distinct_admissions', COUNT(DISTINCT hadm_id) FROM base
    UNION ALL
    SELECT 'distinct_stays', COUNT(DISTINCT stay_id) FROM base
    UNION ALL
    SELECT 'duplicate_stay_rows', COUNT(*) - COUNT(DISTINCT stay_id) FROM base
    UNION ALL
    SELECT 'subjects_with_repeated_admissions', COUNT(*) FROM repeated
    UNION ALL
    SELECT 'eligible_primary_analysis', COUNTIF(eligible_primary_analysis = 1) FROM base
    UNION ALL
    SELECT 'eligible_include_massive_transfusion_sensitivity',
           COUNTIF(eligible_include_massive_transfusion_sensitivity = 1) FROM base
    UNION ALL
    SELECT 'eligible_sensitivity_48h_los', COUNTIF(eligible_sensitivity_48h_los = 1) FROM base
    UNION ALL
    SELECT 'eligible_no_transfusion_sensitivity', COUNTIF(eligible_no_transfusion_sensitivity = 1) FROM base
    UNION ALL
    SELECT 'deaths_before_feature_window_end',
           COUNTIF(hospital_mortality = 1 AND deathtime < feature_window_end) FROM base
    UNION ALL
    SELECT 'discharges_before_feature_window_end', COUNTIF(dischtime < feature_window_end) FROM base
    UNION ALL
    SELECT 'invalid_feature_window_end',
           COUNTIF(feature_window_end != DATETIME_ADD(icu_intime, INTERVAL 48 HOUR)) FROM base
)
SELECT
    metric,
    metric_value,
    CURRENT_TIMESTAMP() AS checked_at_utc,
    CASE
        WHEN metric IN ('duplicate_stay_rows', 'invalid_feature_window_end') AND metric_value != 0 THEN 'FAIL'
        ELSE 'REVIEW'
    END AS qc_status
FROM metrics;

-- Expected grain: one row per stay_id. These queries return aggregates only.
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.freeze_release_qc_summary`
ORDER BY metric;

-- Verify the exact source schemas and table metadata visible during the freeze run.
SELECT
    table_catalog,
    table_schema,
    table_name,
    table_type,
    creation_time
FROM `physionet-data.mimiciv_3_1_derived.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN (
    'complete_blood_count', 'chemistry', 'gcs', 'vitalsign', 'bg',
    'first_day_sofa', 'sapsii', 'apsiii', 'oasis', 'lods'
)
ORDER BY table_name;

-- Aggregate dictionary audit for diagnosis rules; no patient identifiers are returned.
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.freeze_diagnosis_code_audit` AS
SELECT
    di.icd_version,
    di.icd_code,
    dd.long_title,
    CASE
        WHEN di.icd_version = 9 AND REPLACE(UPPER(di.icd_code), '.', '') LIKE '430%' THEN 'include_sah'
        WHEN di.icd_version = 10 AND REPLACE(UPPER(di.icd_code), '.', '') LIKE 'I60%' THEN 'include_sah'
        WHEN di.icd_version = 10 AND REPLACE(UPPER(di.icd_code), '.', '') LIKE 'S066%' THEN 'exclude_traumatic_sah'
        WHEN LOWER(dd.long_title) LIKE '%traumatic%subarachnoid%'
         AND LOWER(dd.long_title) NOT LIKE '%nontraumatic%subarachnoid%'
         AND LOWER(dd.long_title) NOT LIKE '%non-traumatic%subarachnoid%' THEN 'exclude_traumatic_title'
        ELSE 'other'
    END AS rule_action,
    COUNT(DISTINCT di.hadm_id) AS admissions
FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
LEFT JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
    ON di.icd_code = dd.icd_code
   AND di.icd_version = dd.icd_version
WHERE (di.icd_version = 9 AND REPLACE(UPPER(di.icd_code), '.', '') LIKE '430%')
   OR (di.icd_version = 10 AND REPLACE(UPPER(di.icd_code), '.', '') LIKE 'I60%')
   OR (di.icd_version = 10 AND REPLACE(UPPER(di.icd_code), '.', '') LIKE 'S066%')
   OR LOWER(dd.long_title) LIKE '%traumatic%subarachnoid%'
GROUP BY di.icd_version, di.icd_code, dd.long_title, rule_action;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.freeze_diagnosis_code_audit`
ORDER BY rule_action, icd_version, icd_code;

-- Verify RBC administration item labels and units in the active MIMIC-IV ICU dictionary.
SELECT
    itemid,
    label,
    category,
    unitname,
    linksto
FROM `physionet-data.mimiciv_3_1_icu.d_items`
WHERE itemid IN (225795, 226368)
ORDER BY itemid;
