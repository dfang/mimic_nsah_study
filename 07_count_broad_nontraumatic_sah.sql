-- 统计真正放宽后的 cohort：
-- adult + non-traumatic SAH ICD
--
-- 定义：
--   is_adult = 1
--   has_sah_dx = 1
--   has_traumatic_sah_dx = 0
--
-- 注意：
--   这个定义不再强制要求 aneurysm diagnosis 或 aneurysm procedure evidence。
--   aneurysm evidence 后续只作为验证标记和敏感性分析。

-- 1. 只看诊断层面的 adult + non-traumatic SAH ICD 数量
SELECT
    'adult_nontraumatic_sah_icd' AS cohort_definition,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients,
    COUNTIF(has_aneurysm_dx = 1) AS admissions_with_aneurysm_dx,
    COUNTIF(has_aneurysm_procedure = 1) AS admissions_with_aneurysm_procedure,
    COUNTIF(has_aneurysm_dx = 1 OR has_aneurysm_procedure = 1) AS admissions_with_any_aneurysm_evidence,
    AVG(CAST(hospital_expire_flag AS FLOAT64)) AS hospital_mortality
FROM `mimic-study-498508.asah_study.source_sah_admissions`
WHERE is_adult = 1
  AND has_sah_dx = 1
  AND has_traumatic_sah_dx = 0;

-- 2. 如果用 broad non-traumatic SAH 作为主 cohort，检查已有 physiology_features_48h 中能覆盖多少
-- 当前 physiology_features_48h 是基于旧 strict cohort 生成的，所以这里通常只能反映旧 pipeline 中已有的交集。
-- 若要得到真正 broad cohort 的最终主分析样本量，需要修改 01_create_phenotype_cohort.sql 后重跑。
SELECT
    'broad_nontraumatic_sah_overlap_existing_feature_table' AS cohort_definition,
    COUNT(*) AS feature_rows,
    COUNT(DISTINCT f.subject_id) AS patients,
    COUNTIF(f.core_feature_missing_count <= 2) AS core_missing_le_2,
    COUNTIF(f.core_feature_missing_count <= 2 AND f.massive_transfusion_24h = 0) AS primary_like_rows,
    COUNTIF(f.core_feature_missing_count <= 2 AND f.massive_transfusion_24h = 0 AND f.icu_los_hours >= 48) AS sensitivity_48h_los_rows,
    COUNTIF(f.core_feature_missing_count <= 2 AND f.massive_transfusion_24h = 0 AND f.any_rbc_transfusion_48h = 0) AS no_transfusion_rows
FROM `mimic-study-498508.asah_study.source_sah_admissions` s
INNER JOIN `mimic-study-498508.asah_study.physiology_features_48h` f
    ON s.subject_id = f.subject_id
   AND s.hadm_id = f.hadm_id
WHERE s.is_adult = 1
  AND s.has_sah_dx = 1
  AND s.has_traumatic_sah_dx = 0;

