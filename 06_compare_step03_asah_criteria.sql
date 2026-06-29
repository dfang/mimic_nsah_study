-- 比较第 3 步 aSAH 证据规则对样本量的影响
--
-- 当前规则：
--   SAH + aneurysm diagnosis OR aneurysm procedure evidence
--   即 asah_evidence_level >= 2
--
-- 你想看的规则：
--   SAH + aneurysm diagnosis
--   即 has_aneurysm_dx = 1
--
-- 注意：
--   如果只要求 aneurysm diagnosis，而不接受 procedure-only evidence，
--   这通常不是放宽，而是比当前 OR 规则更严格或相等。

-- 1. 成人 SAH 候选人群中，对比不同第 3 步规则的样本量
SELECT
    '02_adult_sah' AS rule,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients
FROM `mimic-study-498508.ash_study.source_sah_admissions`
WHERE is_adult = 1

UNION ALL

SELECT
    '03a_SAH_plus_aneurysm_diagnosis_only' AS rule,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients
FROM `mimic-study-498508.ash_study.source_sah_admissions`
WHERE is_adult = 1
  AND has_sah_dx = 1
  AND has_aneurysm_dx = 1

UNION ALL

SELECT
    '03b_SAH_plus_aneurysm_procedure_only' AS rule,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients
FROM `mimic-study-498508.ash_study.source_sah_admissions`
WHERE is_adult = 1
  AND has_sah_dx = 1
  AND has_aneurysm_dx = 0
  AND has_aneurysm_procedure = 1

UNION ALL

SELECT
    '03c_current_SAH_plus_dx_or_procedure' AS rule,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients
FROM `mimic-study-498508.ash_study.source_sah_admissions`
WHERE is_adult = 1
  AND has_sah_dx = 1
  AND (has_aneurysm_dx = 1 OR has_aneurysm_procedure = 1)

UNION ALL

SELECT
    '03d_broad_nontraumatic_SAH_no_extra_aneurysm_required' AS rule,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients
FROM `mimic-study-498508.ash_study.source_sah_admissions`
WHERE is_adult = 1
  AND has_sah_dx = 1
  AND has_traumatic_sah_dx = 0
ORDER BY rule;

-- 2. 如果第 3 步改为“SAH plus aneurysm diagnosis only”，后续主分析能剩多少
--    这里复用已经生成的 physiology_features_48h，只统计能进入后续特征宽表的病例。
SELECT
    'dx_only_after_feature_pipeline' AS rule,
    COUNT(*) AS feature_rows,
    COUNT(DISTINCT subject_id) AS patients,
    COUNTIF(core_feature_missing_count <= 2) AS core_missing_le_2,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0) AS primary_like_rows,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0 AND icu_los_hours >= 48) AS sensitivity_48h_los_rows,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0 AND any_rbc_transfusion_48h = 0) AS no_transfusion_rows
FROM `mimic-study-498508.ash_study.physiology_features_48h`
WHERE has_aneurysm_dx = 1;

-- 3. 当前 OR 规则中，diagnosis-only、procedure-only、both 的构成
SELECT
    CASE
        WHEN has_aneurysm_dx = 1 AND has_aneurysm_procedure = 1 THEN 'both_dx_and_procedure'
        WHEN has_aneurysm_dx = 1 AND has_aneurysm_procedure = 0 THEN 'dx_only'
        WHEN has_aneurysm_dx = 0 AND has_aneurysm_procedure = 1 THEN 'procedure_only'
        ELSE 'neither'
    END AS evidence_pattern,
    COUNT(*) AS admissions,
    COUNT(DISTINCT subject_id) AS patients
FROM `mimic-study-498508.ash_study.source_sah_admissions`
WHERE is_adult = 1
  AND has_sah_dx = 1
GROUP BY evidence_pattern
ORDER BY admissions DESC;

