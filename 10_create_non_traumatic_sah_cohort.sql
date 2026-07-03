-- non-traumatic SAH 早期多模态生理表型 cohort 构建脚本
-- 数据源：MIMIC-IV 3.1 BigQuery
--   原始数据：physionet-data.mimiciv_3_1_hosp, physionet-data.mimiciv_3_1_icu
--   衍生数据：physionet-data.mimiciv_3_1_derived
-- 目标位置：mimic-study-498508.non_traumatic_sah_study
--
-- 设计原则：
-- 1. 先宽后严：先保留候选人群和筛选标记，再生成主分析 cohort。
-- 2. 时间锚点：首次 ICU 入科时间 icu_intime。
-- 3. 主窗口：ICU 入科后 0-48 小时；敏感性窗口可复用明细表改成 0-24 小时。
-- 4. 主聚类变量：Hb、total GCS、GCS motor、MAP、shock index、SpO2、creatinine、platelet。
--    Lactate 和 PaO2/FiO2 因当前 cohort 缺失率高，仅保留为描述/敏感性变量，不进入主聚类或 eligibility 缺失计数。
-- 5. 每个关键步骤后都附带验证查询，便于检查样本量、唯一性、覆盖率和异常值。

-- 目的：创建本研究专用数据集。
-- 原因：所有 cohort 中间表和最终宽表统一存储，方便复现、排查和清理。
CREATE SCHEMA IF NOT EXISTS `mimic-study-498508.non_traumatic_sah_study`
OPTIONS(location = 'US');

-- 验证：确认目标 project 和 dataset。
SELECT
    'mimic-study-498508' AS project_id,
    'non_traumatic_sah_study' AS dataset_id,
    'non-traumatic SAH 早期多模态生理表型研究' AS study_note;

-- 验证：确认本脚本依赖的 derived 表和关键字段存在。
-- 原因：不同 MIMIC-IV BigQuery 发布路径可能有细小列名差异，先查 schema 可避免跑到中途才失败。
SELECT
    table_name,
    STRING_AGG(column_name, ', ' ORDER BY column_name) AS available_columns
FROM `physionet-data.mimiciv_3_1_derived.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('complete_blood_count', 'chemistry', 'gcs', 'vitalsign', 'bg')
  AND column_name IN (
      'subject_id', 'hadm_id', 'stay_id', 'charttime',
      'hemoglobin', 'hematocrit', 'platelet', 'creatinine', 'gcs', 'gcs_motor',
      'heart_rate', 'sbp', 'sbp_ni', 'mbp', 'mbp_ni',
      'spo2', 'lactate', 'po2', 'pao2fio2ratio'
  )
GROUP BY table_name
ORDER BY table_name;

-- -----------------------------------------------------------------------------
-- 1. 诊断与操作证据：建立 SAH/non-traumatic SAH 候选住院
-- -----------------------------------------------------------------------------

-- 目的：提取 SAH 诊断、动脉瘤诊断和创伤性 SAH 诊断标记。
-- 原因：单独 SAH ICD 不能保证是动脉瘤性 SAH，需要逐层保留诊断证据。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.dx_sah_flags` AS
SELECT
    di.subject_id,
    di.hadm_id,
    MAX(
        CASE
            WHEN di.icd_version = 9 AND di.icd_code LIKE '430%' THEN 1
            WHEN di.icd_version = 10 AND di.icd_code LIKE 'I60%' THEN 1
            ELSE 0
        END
    ) AS has_sah_dx,
    MAX(
        CASE
            WHEN di.icd_version = 9 AND di.icd_code = '437.3' THEN 1
            WHEN di.icd_version = 10 AND di.icd_code LIKE 'I67.1%' THEN 1
            ELSE 0
        END
    ) AS has_aneurysm_dx,
    MAX(
        CASE
            WHEN di.icd_version = 10 AND di.icd_code LIKE 'S06.6%' THEN 1
            WHEN LOWER(dd.long_title) LIKE '%nontraumatic%subarachnoid%' THEN 0
            WHEN LOWER(dd.long_title) LIKE '%non-traumatic%subarachnoid%' THEN 0
            WHEN LOWER(dd.long_title) LIKE '%traumatic%subarachnoid%' THEN 1
            ELSE 0
        END
    ) AS has_traumatic_sah_dx
FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
LEFT JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses` dd
    ON di.icd_code = dd.icd_code
   AND di.icd_version = dd.icd_version
GROUP BY di.subject_id, di.hadm_id;

-- 验证：检查 SAH、动脉瘤和创伤性 SAH 诊断标记数量。
SELECT
    COUNT(*) AS diagnosis_admissions,
    COUNTIF(has_sah_dx = 1) AS sah_admissions,
    COUNTIF(has_aneurysm_dx = 1) AS aneurysm_dx_admissions,
    COUNTIF(has_sah_dx = 1 AND has_aneurysm_dx = 1) AS sah_with_aneurysm_dx,
    COUNTIF(has_sah_dx = 1 AND has_traumatic_sah_dx = 1) AS sah_with_traumatic_flag
FROM `mimic-study-498508.non_traumatic_sah_study.dx_sah_flags`;

-- 目的：从操作代码字典中识别 clipping/coiling/endovascular embolization 等动脉瘤处置候选。
-- 原因：处置证据可作为更高特异性的 non-traumatic SAH 识别标准和敏感性分析依据。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.aneurysm_procedure_flags` AS
SELECT
    pi.subject_id,
    pi.hadm_id,
    1 AS has_aneurysm_procedure,
    STRING_AGG(DISTINCT pi.icd_code, ', ' ORDER BY pi.icd_code) AS aneurysm_procedure_codes
FROM `physionet-data.mimiciv_3_1_hosp.procedures_icd` pi
INNER JOIN `physionet-data.mimiciv_3_1_hosp.d_icd_procedures` dp
    ON pi.icd_code = dp.icd_code
   AND pi.icd_version = dp.icd_version
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
GROUP BY pi.subject_id, pi.hadm_id;

-- 验证：查看操作证据数量和候选操作代码样例。
SELECT
    COUNT(*) AS admissions_with_aneurysm_procedure,
    COUNT(DISTINCT subject_id) AS patients_with_aneurysm_procedure
FROM `mimic-study-498508.non_traumatic_sah_study.aneurysm_procedure_flags`;

SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.aneurysm_procedure_flags`
ORDER BY subject_id, hadm_id
LIMIT 10;

-- 目的：建立宽松 SAH/non-traumatic SAH 候选住院表，并保留诊断层级。
-- 原因：后续 flowchart 和敏感性分析需要知道每个住院满足哪一档 non-traumatic SAH 定义。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.source_sah_admissions` AS
SELECT
    a.subject_id,
    a.hadm_id,
    a.admittime,
    a.dischtime,
    a.deathtime,
    a.admission_type,
    a.race,
    a.insurance,
    a.hospital_expire_flag,
    p.anchor_age AS age,
    p.gender,
    COALESCE(dx.has_sah_dx, 0) AS has_sah_dx,
    COALESCE(dx.has_aneurysm_dx, 0) AS has_aneurysm_dx,
    COALESCE(proc.has_aneurysm_procedure, 0) AS has_aneurysm_procedure,
    COALESCE(dx.has_traumatic_sah_dx, 0) AS has_traumatic_sah_dx,
    proc.aneurysm_procedure_codes,
    CASE
        WHEN COALESCE(dx.has_sah_dx, 0) = 1
         AND COALESCE(proc.has_aneurysm_procedure, 0) = 1 THEN 3
        WHEN COALESCE(dx.has_sah_dx, 0) = 1
         AND COALESCE(dx.has_aneurysm_dx, 0) = 1 THEN 2
        WHEN COALESCE(dx.has_sah_dx, 0) = 1 THEN 1
        ELSE 0
    END AS nsah_evidence_level,
    CASE WHEN p.anchor_age >= 18 THEN 1 ELSE 0 END AS is_adult
FROM `physionet-data.mimiciv_3_1_hosp.admissions` a
INNER JOIN `physionet-data.mimiciv_3_1_hosp.patients` p
    ON a.subject_id = p.subject_id
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.dx_sah_flags` dx
    ON a.subject_id = dx.subject_id
   AND a.hadm_id = dx.hadm_id
LEFT JOIN `mimic-study-498508.non_traumatic_sah_study.aneurysm_procedure_flags` proc
    ON a.subject_id = proc.subject_id
   AND a.hadm_id = proc.hadm_id
WHERE COALESCE(dx.has_sah_dx, 0) = 1;

-- 验证：检查 SAH 候选住院数量、成人比例和 non-traumatic SAH 证据层级分布。
SELECT
    COUNT(*) AS source_sah_rows,
    COUNT(DISTINCT subject_id) AS source_sah_patients,
    COUNT(DISTINCT hadm_id) AS source_sah_admissions,
    COUNTIF(is_adult = 1) AS adult_admissions,
    COUNTIF(nsah_evidence_level >= 2) AS strict_nsah_admissions,
    COUNTIF(nsah_evidence_level = 3) AS procedure_confirmed_admissions,
    COUNTIF(has_traumatic_sah_dx = 1) AS traumatic_sah_flagged
FROM `mimic-study-498508.non_traumatic_sah_study.source_sah_admissions`;

SELECT
    nsah_evidence_level,
    COUNT(*) AS admissions
FROM `mimic-study-498508.non_traumatic_sah_study.source_sah_admissions`
GROUP BY nsah_evidence_level
ORDER BY nsah_evidence_level;

-- 目的：生成主分析候选 non-traumatic SAH 住院。
-- 原因：本研究范围从 aSAH 放宽为 non-traumatic SAH；因此保留成人 SAH、排除明显创伤性 SAH，
--       但不再要求动脉瘤诊断或动脉瘤处置证据。其余流程尽量与 01_create_phenotype_cohort.sql 保持一致。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.confirmed_nsah_admissions` AS
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.source_sah_admissions`
WHERE is_adult = 1
  AND has_sah_dx = 1
  AND has_traumatic_sah_dx = 0;

-- 验证：检查主分析候选 non-traumatic SAH 住院规模和唯一性。
SELECT
    COUNT(*) AS confirmed_rows,
    COUNT(DISTINCT subject_id) AS confirmed_patients,
    COUNT(DISTINCT hadm_id) AS confirmed_admissions,
    COUNT(*) - COUNT(DISTINCT CONCAT(CAST(subject_id AS STRING), '-', CAST(hadm_id AS STRING))) AS duplicate_subject_hadm_rows,
    AVG(CAST(hospital_expire_flag AS FLOAT64)) AS hospital_mortality_rate
FROM `mimic-study-498508.non_traumatic_sah_study.confirmed_nsah_admissions`;

-- -----------------------------------------------------------------------------
-- 2. 首次 ICU stay 与基础 eligible cohort
-- -----------------------------------------------------------------------------

-- 目的：为每次 non-traumatic SAH 住院选择首次 ICU stay。
-- 原因：首次 ICU stay 最接近入院早期状态，避免重复 ICU stay 和治疗后状态污染。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.first_icu_nsah_stays` AS
WITH ranked AS (
    SELECT
        ca.subject_id,
        ca.hadm_id,
        ie.stay_id,
        ca.admittime,
        ca.dischtime,
        ca.deathtime,
        ca.admission_type,
        ca.race,
        ca.insurance,
        ca.hospital_expire_flag,
        ca.age,
        ca.gender,
        ca.nsah_evidence_level,
        ca.has_aneurysm_dx,
        ca.has_aneurysm_procedure,
        ie.intime AS icu_intime,
        ie.outtime AS icu_outtime,
        DATETIME_DIFF(ie.outtime, ie.intime, HOUR) AS icu_los_hours,
        DATETIME_DIFF(ca.dischtime, ca.admittime, HOUR) / 24.0 AS hospital_los_days,
        ROW_NUMBER() OVER (
            PARTITION BY ca.subject_id, ca.hadm_id
            ORDER BY ie.intime ASC
        ) AS icu_sequence
    FROM `mimic-study-498508.non_traumatic_sah_study.confirmed_nsah_admissions` ca
    INNER JOIN `physionet-data.mimiciv_3_1_icu.icustays` ie
        ON ca.subject_id = ie.subject_id
       AND ca.hadm_id = ie.hadm_id
)
SELECT
    *,
    CASE WHEN icu_sequence = 1 THEN 1 ELSE 0 END AS is_first_icu_stay,
    CASE WHEN icu_los_hours >= 24 THEN 1 ELSE 0 END AS icu_los_ge_24h,
    CASE WHEN icu_los_hours >= 48 THEN 1 ELSE 0 END AS icu_los_ge_48h,
    CASE
        WHEN deathtime IS NOT NULL
         AND deathtime >= icu_intime
         AND deathtime <= icu_outtime THEN 1
        ELSE 0
    END AS icu_mortality
FROM ranked
WHERE icu_sequence = 1;

-- 验证：检查首次 ICU stay 数量、ICU 时长分布和短 stay 数量。
SELECT
    COUNT(*) AS first_icu_rows,
    COUNT(DISTINCT subject_id) AS patients,
    COUNT(DISTINCT hadm_id) AS admissions,
    COUNT(DISTINCT stay_id) AS stays,
    COUNTIF(icu_los_hours < 24) AS stays_lt_24h,
    COUNTIF(icu_los_hours >= 24 AND icu_los_hours < 48) AS stays_24_to_48h,
    COUNTIF(icu_los_hours >= 48) AS stays_ge_48h,
    MIN(icu_los_hours) AS min_icu_los_hours,
    APPROX_QUANTILES(icu_los_hours, 4)[OFFSET(2)] AS median_icu_los_hours,
    MAX(icu_los_hours) AS max_icu_los_hours
FROM `mimic-study-498508.non_traumatic_sah_study.first_icu_nsah_stays`;

-- 验证：确认每个 stay_id 只出现一次。
SELECT
    stay_id,
    COUNT(*) AS row_count
FROM `mimic-study-498508.non_traumatic_sah_study.first_icu_nsah_stays`
GROUP BY stay_id
HAVING COUNT(*) > 1;

-- 目的：生成基础 eligible cohort，暂时只限定 ICU stay >=24h。
-- 原因：核心特征缺失、输血等条件应在宽表中保留标记后再筛选，避免过早删除样本。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` AS
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.first_icu_nsah_stays`
WHERE icu_los_ge_24h = 1;

-- 验证：检查基础 eligible cohort 规模和结局。
SELECT
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT subject_id) AS eligible_patients,
    COUNT(DISTINCT stay_id) AS eligible_stays,
    AVG(CAST(hospital_expire_flag AS FLOAT64)) AS hospital_mortality_rate,
    AVG(CAST(icu_mortality AS FLOAT64)) AS icu_mortality_rate,
    AVG(icu_los_hours) / 24.0 AS mean_icu_los_days
FROM `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort`;

-- -----------------------------------------------------------------------------
-- 3. 红细胞输血标记：作为排除/敏感性分析因素，不作为核心暴露
-- -----------------------------------------------------------------------------

-- 目的：核对 RBC/PRBC 输血 itemid 候选。
-- 原因：MIMIC-IV 版本差异可能影响 itemid，正式分析前应人工确认。
SELECT
    itemid,
    label,
    abbreviation,
    category,
    unitname
FROM `physionet-data.mimiciv_3_1_icu.d_items`
WHERE LOWER(label) LIKE '%red blood cell%'
   OR LOWER(label) LIKE '%prbc%'
ORDER BY itemid;

-- 目的：提取 ICU 入科后 0-48h 的 RBC 输血事件。
-- 原因：输血会影响 Hb 和循环状态，需要标记普通输血与大量输血。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.rbc_transfusion_0_48h` AS
SELECT
    ie.subject_id,
    ie.hadm_id,
    ie.stay_id,
    ie.starttime AS transfusion_time,
    DATETIME_DIFF(ie.starttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    ie.itemid,
    ie.amount,
    ie.amountuom,
    ie.statusdescription
FROM `physionet-data.mimiciv_3_1_icu.inputevents` ie
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON ie.subject_id = c.subject_id
   AND ie.hadm_id = c.hadm_id
   AND ie.stay_id = c.stay_id
WHERE ie.itemid IN (225795, 226368)
  AND ie.starttime >= c.icu_intime
  AND ie.starttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR)
  AND ie.statusdescription != 'Rewritten'
  AND ie.amount > 0;

-- 验证：检查 RBC 输血事件数、患者数、时间范围和单位。
SELECT
    COUNT(*) AS rbc_event_count,
    COUNT(DISTINCT stay_id) AS stays_with_rbc,
    MIN(hours_from_icu_intime) AS min_hours,
    MAX(hours_from_icu_intime) AS max_hours,
    STRING_AGG(DISTINCT amountuom, ', ' ORDER BY amountuom) AS amount_units
FROM `mimic-study-498508.non_traumatic_sah_study.rbc_transfusion_0_48h`;

-- 目的：按 stay 汇总 0-24h 和 0-48h 输血标记。
-- 原因：主分析排除大量输血，敏感性分析可排除所有输血患者。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.rbc_transfusion_flags` AS
SELECT
    c.subject_id,
    c.hadm_id,
    c.stay_id,
    MIN(t.transfusion_time) AS first_rbc_time_48h,
    COUNT(t.transfusion_time) AS rbc_events_48h,
    COUNTIF(t.hours_from_icu_intime < 24) AS rbc_events_24h,
    SUM(
        CASE
            WHEN LOWER(COALESCE(t.amountuom, '')) LIKE '%unit%' THEN t.amount
            ELSE NULL
        END
    ) AS rbc_units_48h,
    SUM(
        CASE
            WHEN t.hours_from_icu_intime < 24
             AND LOWER(COALESCE(t.amountuom, '')) LIKE '%unit%' THEN t.amount
            ELSE NULL
        END
    ) AS rbc_units_24h,
    CASE WHEN COUNT(t.transfusion_time) > 0 THEN 1 ELSE 0 END AS any_rbc_transfusion_48h,
    CASE
        WHEN COUNTIF(t.hours_from_icu_intime < 24) >= 5 THEN 1
        WHEN SUM(
            CASE
                WHEN t.hours_from_icu_intime < 24
                 AND LOWER(COALESCE(t.amountuom, '')) LIKE '%unit%' THEN t.amount
                ELSE 0
            END
        ) >= 5 THEN 1
        ELSE 0
    END AS massive_transfusion_24h
FROM `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
LEFT JOIN `mimic-study-498508.non_traumatic_sah_study.rbc_transfusion_0_48h` t
    ON c.stay_id = t.stay_id
GROUP BY c.subject_id, c.hadm_id, c.stay_id;

-- 验证：检查普通输血和大量输血标记。
SELECT
    COUNT(*) AS cohort_stays,
    COUNTIF(any_rbc_transfusion_48h = 1) AS stays_with_any_rbc_48h,
    COUNTIF(massive_transfusion_24h = 1) AS stays_with_massive_rbc_24h,
    MIN(rbc_events_48h) AS min_rbc_events_48h,
    MAX(rbc_events_48h) AS max_rbc_events_48h
FROM `mimic-study-498508.non_traumatic_sah_study.rbc_transfusion_flags`;

-- -----------------------------------------------------------------------------
-- 4. 0-48h 核心生理指标明细表
-- -----------------------------------------------------------------------------

-- 目的：提取 0-48h Hb 明细，并标记是否发生在首次 RBC 输血前。
-- 原因：Hb 是贫血定义和聚类变量，输血后 Hb 可能被治疗改变。
--       优先使用 MIMIC-IV derived.complete_blood_count，避免重复手写 CBC itemid 映射。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.hb_0_48h` AS
SELECT
    cbc.subject_id,
    cbc.hadm_id,
    c.stay_id,
    cbc.charttime,
    DATETIME_DIFF(cbc.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.complete_blood_count' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    cbc.hemoglobin AS hb
FROM `physionet-data.mimiciv_3_1_derived.complete_blood_count` cbc
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON cbc.subject_id = c.subject_id
   AND cbc.hadm_id = c.hadm_id
WHERE cbc.hemoglobin > 3
  AND cbc.hemoglobin < 25
  AND cbc.charttime >= c.icu_intime
  AND cbc.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：Hb 覆盖率、范围和窗口。
SELECT
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(hb) AS min_hb,
    APPROX_QUANTILES(hb, 4)[OFFSET(2)] AS median_hb,
    MAX(hb) AS max_hb,
    MIN(hours_from_icu_intime) AS min_hours,
    MAX(hours_from_icu_intime) AS max_hours
FROM `mimic-study-498508.non_traumatic_sah_study.hb_0_48h`;

-- 目的：提取 0-48h 估算血浆容量状态 ePVS。
-- 原因：ePVS 可由 CBC 中 Hb/Hct 计算，作为容量状态候选增强变量；先保留用于覆盖率审计，
--       不在未验证缺失率和分布前纳入主聚类。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.epvs_0_48h` AS
WITH cbc_clean AS (
    SELECT
        cbc.subject_id,
        cbc.hadm_id,
        c.stay_id,
        cbc.charttime,
        DATETIME_DIFF(cbc.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
        'mimiciv_3_1_derived.complete_blood_count' AS source_table,
        c.gender,
        cbc.hemoglobin AS hb_g_dl,
        CASE
            WHEN cbc.hematocrit BETWEEN 0.10 AND 0.70 THEN cbc.hematocrit
            WHEN cbc.hematocrit BETWEEN 10 AND 70 THEN cbc.hematocrit / 100.0
            ELSE NULL
        END AS hct_fraction
    FROM `physionet-data.mimiciv_3_1_derived.complete_blood_count` cbc
    INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
        ON cbc.subject_id = c.subject_id
       AND cbc.hadm_id = c.hadm_id
    WHERE cbc.hemoglobin BETWEEN 3 AND 25
      AND cbc.hematocrit IS NOT NULL
      AND cbc.charttime >= c.icu_intime
      AND cbc.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR)
)
SELECT
    subject_id,
    hadm_id,
    stay_id,
    charttime,
    hours_from_icu_intime,
    source_table,
    hb_g_dl,
    hct_fraction,
    CASE WHEN gender = 'M' THEN 150.0 ELSE 130.0 END AS expected_hb_g_l,
    CASE WHEN gender = 'M' THEN 0.46 ELSE 0.42 END AS expected_hct_fraction,
    ((hb_g_dl * 10.0) / (CASE WHEN gender = 'M' THEN 150.0 ELSE 130.0 END))
      - (hct_fraction / (CASE WHEN gender = 'M' THEN 0.46 ELSE 0.42 END)) AS epvs
FROM cbc_clean
WHERE hct_fraction BETWEEN 0.10 AND 0.70;

-- 验证：ePVS 覆盖率和范围。
SELECT
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(epvs) AS min_epvs,
    APPROX_QUANTILES(epvs, 4)[OFFSET(2)] AS median_epvs,
    MAX(epvs) AS max_epvs
FROM `mimic-study-498508.non_traumatic_sah_study.epvs_0_48h`;

-- 目的：提取 0-48h total GCS、GCS grade 和 GCS motor 明细。
-- 原因：主聚类使用 total GCS 和 GCS motor 表征神经严重度；
--       GCS grade 保留为描述、分层和敏感性分析变量。
--       derived.gcs 已统一 GCS components，优先于直接读取 chartevents itemid。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.gcs_0_48h` AS
SELECT
    g.subject_id,
    c.hadm_id,
    g.stay_id,
    g.charttime,
    DATETIME_DIFF(g.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.gcs' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    g.gcs AS gcs_total,
    CASE
        WHEN g.gcs BETWEEN 3 AND 8 THEN 3
        WHEN g.gcs BETWEEN 9 AND 12 THEN 2
        WHEN g.gcs BETWEEN 13 AND 15 THEN 1
        ELSE NULL
    END AS gcs_grade,
    g.gcs_motor AS gcs_motor
FROM `physionet-data.mimiciv_3_1_derived.gcs` g
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON g.stay_id = c.stay_id
WHERE (g.gcs BETWEEN 3 AND 15 OR g.gcs_motor BETWEEN 1 AND 6)
  AND g.charttime >= c.icu_intime
  AND g.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：GCS 覆盖率和范围。
SELECT
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(gcs_total) AS min_gcs_total,
    MAX(gcs_total) AS max_gcs_total,
    MIN(gcs_grade) AS min_gcs_grade,
    MAX(gcs_grade) AS max_gcs_grade,
    MIN(gcs_motor) AS min_gcs_motor,
    MAX(gcs_motor) AS max_gcs_motor
FROM `mimic-study-498508.non_traumatic_sah_study.gcs_0_48h`;

-- 目的：提取 0-48h MAP 明细。
-- 原因：最低 MAP 反映早期循环灌注最差状态。
--       derived.vitalsign 已整合有创/无创血压字段，减少手工 itemid 漏提。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.map_0_48h` AS
SELECT
    vs.subject_id,
    c.hadm_id,
    vs.stay_id,
    vs.charttime,
    DATETIME_DIFF(vs.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.vitalsign' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    COALESCE(vs.mbp, vs.mbp_ni) AS map_value
FROM `physionet-data.mimiciv_3_1_derived.vitalsign` vs
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON vs.stay_id = c.stay_id
WHERE COALESCE(vs.mbp, vs.mbp_ni) BETWEEN 30 AND 200
  AND vs.charttime >= c.icu_intime
  AND vs.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：MAP 覆盖率和范围。
SELECT
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(map_value) AS min_map,
    MAX(map_value) AS max_map
FROM `mimic-study-498508.non_traumatic_sah_study.map_0_48h`;

-- 目的：提取 0-48h 心率和收缩压明细。
-- 原因：shock index = HR / SBP，需要先分别清洗 HR 与 SBP。
--       derived.vitalsign 统一了常用生命体征，优先于 chartevents itemid。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.heart_rate_0_48h` AS
SELECT
    vs.subject_id,
    c.hadm_id,
    vs.stay_id,
    vs.charttime,
    DATETIME_DIFF(vs.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.vitalsign' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    vs.heart_rate
FROM `physionet-data.mimiciv_3_1_derived.vitalsign` vs
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON vs.stay_id = c.stay_id
WHERE vs.heart_rate BETWEEN 30 AND 220
  AND vs.charttime >= c.icu_intime
  AND vs.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.sbp_0_48h` AS
SELECT
    vs.subject_id,
    c.hadm_id,
    vs.stay_id,
    vs.charttime,
    DATETIME_DIFF(vs.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.vitalsign' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    COALESCE(vs.sbp, vs.sbp_ni) AS sbp
FROM `physionet-data.mimiciv_3_1_derived.vitalsign` vs
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON vs.stay_id = c.stay_id
WHERE COALESCE(vs.sbp, vs.sbp_ni) BETWEEN 50 AND 260
  AND vs.charttime >= c.icu_intime
  AND vs.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：HR/SBP 覆盖率。
SELECT
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.heart_rate_0_48h`) AS stays_with_hr,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.sbp_0_48h`) AS stays_with_sbp,
    (SELECT COUNT(*) FROM `mimic-study-498508.non_traumatic_sah_study.heart_rate_0_48h`) AS hr_measurements,
    (SELECT COUNT(*) FROM `mimic-study-498508.non_traumatic_sah_study.sbp_0_48h`) AS sbp_measurements;

-- 目的：使用 HR 前后 30 分钟内最近 SBP 计算 shock index。
-- 原因：HR 和 SBP 不一定同一 charttime，近邻匹配比强制同一时刻覆盖率更高。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.shock_index_0_48h` AS
WITH matched AS (
    SELECT
        hr.subject_id,
        hr.hadm_id,
        hr.stay_id,
        hr.charttime AS hr_time,
        sbp.charttime AS sbp_time,
        hr.heart_rate,
        sbp.sbp,
        hr.heart_rate / NULLIF(sbp.sbp, 0) AS shock_index,
        ABS(DATETIME_DIFF(hr.charttime, sbp.charttime, MINUTE)) AS time_diff_minutes,
        ROW_NUMBER() OVER (
            PARTITION BY hr.stay_id, hr.charttime
            ORDER BY ABS(DATETIME_DIFF(hr.charttime, sbp.charttime, MINUTE)) ASC
        ) AS rn
    FROM `mimic-study-498508.non_traumatic_sah_study.heart_rate_0_48h` hr
    INNER JOIN `mimic-study-498508.non_traumatic_sah_study.sbp_0_48h` sbp
        ON hr.stay_id = sbp.stay_id
       AND sbp.charttime BETWEEN DATETIME_SUB(hr.charttime, INTERVAL 30 MINUTE)
                            AND DATETIME_ADD(hr.charttime, INTERVAL 30 MINUTE)
)
SELECT *
FROM matched
WHERE rn = 1
  AND shock_index BETWEEN 0.1 AND 5;

-- 验证：shock index 匹配覆盖率和时间差。
SELECT
    COUNT(*) AS matched_rows,
    COUNT(DISTINCT stay_id) AS stays_with_shock_index,
    MIN(shock_index) AS min_shock_index,
    MAX(shock_index) AS max_shock_index,
    MIN(time_diff_minutes) AS min_time_diff_minutes,
    MAX(time_diff_minutes) AS max_time_diff_minutes
FROM `mimic-study-498508.non_traumatic_sah_study.shock_index_0_48h`;

-- 目的：提取 0-48h 乳酸、肌酐、血小板明细。
-- 原因：三者分别反映组织灌注、肾功能和凝血/炎症状态。
--       乳酸优先使用官方 mimiciv_3_1_derived.bg，并以原始 labevents 50813 兜底。
--       bg 表按血气标本整合结果，可补回部分 hadm_id 为空或同一血气标本中的乳酸；
--       chartevents 不作为主乳酸来源，避免把床旁记录标签误当作检验结果。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.lactate_0_48h` AS
WITH bg_lactate AS (
    SELECT
        bg.subject_id,
        COALESCE(bg.hadm_id, c.hadm_id) AS hadm_id,
        c.stay_id,
        bg.charttime,
        DATETIME_DIFF(bg.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
        'mimiciv_3_1_derived.bg' AS source_table,
        CAST(NULL AS INT64) AS source_itemid,
        bg.lactate AS lactate
    FROM `physionet-data.mimiciv_3_1_derived.bg` bg
    INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
        ON bg.subject_id = c.subject_id
       AND (bg.hadm_id = c.hadm_id OR bg.hadm_id IS NULL)
    WHERE bg.lactate > 0
      AND bg.lactate < 30
      AND bg.charttime >= c.icu_intime
      AND bg.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR)
),
lab_lactate AS (
    SELECT
        le.subject_id,
        COALESCE(le.hadm_id, c.hadm_id) AS hadm_id,
        c.stay_id,
        le.charttime,
        DATETIME_DIFF(le.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
        'labevents_50813' AS source_table,
        le.itemid AS source_itemid,
        le.valuenum AS lactate
    FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
    INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
        ON le.subject_id = c.subject_id
       AND (le.hadm_id = c.hadm_id OR le.hadm_id IS NULL)
    WHERE le.itemid = 50813
      AND le.valuenum > 0
      AND le.valuenum < 30
      AND le.charttime >= c.icu_intime
      AND le.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR)
),
all_lactate AS (
    SELECT * FROM bg_lactate
    UNION ALL
    SELECT * FROM lab_lactate
)
SELECT * EXCEPT(source_priority, rn)
FROM (
    SELECT
        *,
        CASE
            WHEN source_table = 'mimiciv_3_1_derived.bg' THEN 1
            ELSE 2
        END AS source_priority,
        ROW_NUMBER() OVER (
            PARTITION BY stay_id, charttime, FORMAT('%.4f', lactate)
            ORDER BY
                CASE
                    WHEN source_table = 'mimiciv_3_1_derived.bg' THEN 1
                    ELSE 2
                END
        ) AS rn
    FROM all_lactate
)
WHERE rn = 1;

-- 目的：提取 0-48h 肌钙蛋白峰值候选变量。
-- 原因：SAH 可出现神经源性心肌损伤；肌钙蛋白用于描述/敏感性分析和覆盖率评估。
--       不同 Troponin I/T assay 单位和量纲可能不同，未标准化前不进入主聚类。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.troponin_labitems` AS
SELECT
    itemid,
    label,
    fluid,
    category
FROM `physionet-data.mimiciv_3_1_hosp.d_labitems`
WHERE LOWER(label) LIKE '%troponin%'
  AND (LOWER(fluid) = 'blood' OR fluid IS NULL);

CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.troponin_0_48h` AS
SELECT
    le.subject_id,
    COALESCE(le.hadm_id, c.hadm_id) AS hadm_id,
    c.stay_id,
    le.charttime,
    DATETIME_DIFF(le.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'hosp.labevents_troponin' AS source_table,
    le.itemid AS source_itemid,
    li.label AS troponin_label,
    le.valueuom AS valueuom,
    le.valuenum AS troponin_value
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.troponin_labitems` li
    ON le.itemid = li.itemid
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON le.subject_id = c.subject_id
   AND (le.hadm_id = c.hadm_id OR le.hadm_id IS NULL)
WHERE le.valuenum IS NOT NULL
  AND le.valuenum >= 0
  AND le.charttime >= c.icu_intime
  AND le.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：肌钙蛋白 assay、单位、覆盖率和范围。
SELECT
    troponin_label,
    valueuom,
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(troponin_value) AS min_troponin,
    APPROX_QUANTILES(troponin_value, 4)[OFFSET(2)] AS median_troponin,
    MAX(troponin_value) AS max_troponin
FROM `mimic-study-498508.non_traumatic_sah_study.troponin_0_48h`
GROUP BY troponin_label, valueuom
ORDER BY stays_covered DESC, troponin_label;

CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.creatinine_0_48h` AS
SELECT
    chem.subject_id,
    chem.hadm_id,
    c.stay_id,
    chem.charttime,
    DATETIME_DIFF(chem.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.chemistry' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    chem.creatinine
FROM `physionet-data.mimiciv_3_1_derived.chemistry` chem
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON chem.subject_id = c.subject_id
   AND chem.hadm_id = c.hadm_id
WHERE chem.creatinine BETWEEN 0.1 AND 20
  AND chem.charttime >= c.icu_intime
  AND chem.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.platelet_0_48h` AS
SELECT
    cbc.subject_id,
    cbc.hadm_id,
    c.stay_id,
    cbc.charttime,
    DATETIME_DIFF(cbc.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.complete_blood_count' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    cbc.platelet
FROM `physionet-data.mimiciv_3_1_derived.complete_blood_count` cbc
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON cbc.subject_id = c.subject_id
   AND cbc.hadm_id = c.hadm_id
WHERE cbc.platelet BETWEEN 10 AND 1000
  AND cbc.charttime >= c.icu_intime
  AND cbc.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：乳酸、肌酐、血小板覆盖率。
SELECT
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.lactate_0_48h`) AS stays_with_lactate,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.lactate_0_48h` WHERE source_table = 'mimiciv_3_1_derived.bg') AS stays_with_bg_lactate,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.lactate_0_48h` WHERE source_table = 'labevents_50813') AS stays_with_labevents_lactate,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.creatinine_0_48h`) AS stays_with_creatinine,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.platelet_0_48h`) AS stays_with_platelet;

-- 目的：提取并清洗 0-48h PaO2、SpO2 和 FiO2。
-- 原因：单纯依赖床旁 SpO2/FiO2 会因为 FiO2 记录缺失而造成较高缺失率；
--       因此优先使用 derived.bg 中已整理的血气 PaO2/FiO2，若不可用再用 SpO2/FiO2 兜底。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.pao2_0_48h` AS
SELECT
    bg.subject_id,
    COALESCE(bg.hadm_id, c.hadm_id) AS hadm_id,
    c.stay_id,
    bg.charttime,
    DATETIME_DIFF(bg.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.bg' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    bg.po2 AS pao2
FROM `physionet-data.mimiciv_3_1_derived.bg` bg
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON bg.subject_id = c.subject_id
   AND (bg.hadm_id = c.hadm_id OR bg.hadm_id IS NULL)
WHERE bg.po2 BETWEEN 20 AND 700
  AND bg.charttime >= c.icu_intime
  AND bg.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.blood_gas_fio2_cleaned_0_48h` AS
SELECT
    le.subject_id,
    le.hadm_id,
    c.stay_id,
    le.charttime,
    DATETIME_DIFF(le.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    le.itemid AS source_itemid,
    le.valuenum AS fio2_raw,
    CASE
        WHEN le.valuenum BETWEEN 0.21 AND 1.0 THEN le.valuenum
        WHEN le.valuenum BETWEEN 21 AND 100 THEN le.valuenum / 100.0
        ELSE NULL
    END AS fio2
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON le.subject_id = c.subject_id
   AND le.hadm_id = c.hadm_id
WHERE le.itemid = 50816
  AND le.valuenum IS NOT NULL
  AND le.charttime >= c.icu_intime
  AND le.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.spo2_0_48h` AS
SELECT
    vs.subject_id,
    c.hadm_id,
    vs.stay_id,
    vs.charttime,
    DATETIME_DIFF(vs.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    'mimiciv_3_1_derived.vitalsign' AS source_table,
    CAST(NULL AS INT64) AS source_itemid,
    vs.spo2
FROM `physionet-data.mimiciv_3_1_derived.vitalsign` vs
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON vs.stay_id = c.stay_id
WHERE vs.spo2 BETWEEN 50 AND 100
  AND vs.charttime >= c.icu_intime
  AND vs.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.fio2_cleaned_0_48h` AS
SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime,
    DATETIME_DIFF(ce.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    ce.itemid AS source_itemid,
    ce.valuenum AS fio2_raw,
    CASE
        WHEN ce.valuenum BETWEEN 0.21 AND 1.0 THEN ce.valuenum
        WHEN ce.valuenum BETWEEN 21 AND 100 THEN ce.valuenum / 100.0
        ELSE NULL
    END AS fio2
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
    ON ce.stay_id = c.stay_id
WHERE ce.itemid = 223835
  AND ce.valuenum IS NOT NULL
  AND ce.charttime >= c.icu_intime
  AND ce.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：FiO2 原始单位模式和清洗后范围。
SELECT
    COUNT(*) AS fio2_rows,
    COUNTIF(fio2_raw BETWEEN 0.21 AND 1.0) AS proportion_style_rows,
    COUNTIF(fio2_raw BETWEEN 21 AND 100) AS percent_style_rows,
    COUNTIF(fio2 IS NULL) AS invalid_fio2_rows,
    MIN(fio2) AS min_clean_fio2,
    MAX(fio2) AS max_clean_fio2
FROM `mimic-study-498508.non_traumatic_sah_study.fio2_cleaned_0_48h`;

-- 目的：用 derived.bg 已计算的 PaO2/FiO2，并以 PaO2 前后 2 小时内最近血气 FiO2 匹配结果兜底。
-- 原因：PaO2/FiO2 是氧合评估的标准指标，优先用于主氧合变量；
--       derived.bg 可减少重复血气清洗和 FiO2 匹配失败造成的缺失。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.pao2_fio2_0_48h` AS
WITH derived_bg AS (
    SELECT
        bg.subject_id,
        COALESCE(bg.hadm_id, c.hadm_id) AS hadm_id,
        c.stay_id,
        bg.charttime AS pao2_time,
        bg.charttime AS fio2_time,
        bg.po2 AS pao2,
        CAST(NULL AS FLOAT64) AS fio2,
        bg.pao2fio2ratio AS pao2_fio2_ratio,
        0 AS time_diff_minutes,
        'mimiciv_3_1_derived.bg' AS source_table
    FROM `physionet-data.mimiciv_3_1_derived.bg` bg
    INNER JOIN `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
        ON bg.subject_id = c.subject_id
       AND (bg.hadm_id = c.hadm_id OR bg.hadm_id IS NULL)
    WHERE bg.pao2fio2ratio BETWEEN 50 AND 700
      AND bg.charttime >= c.icu_intime
      AND bg.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR)
),
matched_raw AS (
    SELECT
        p.subject_id,
        p.hadm_id,
        p.stay_id,
        p.charttime AS pao2_time,
        f.charttime AS fio2_time,
        p.pao2,
        f.fio2,
        p.pao2 / NULLIF(f.fio2, 0) AS pao2_fio2_ratio,
        ABS(DATETIME_DIFF(p.charttime, f.charttime, MINUTE)) AS time_diff_minutes,
        'raw_pao2_fio2_nearest_neighbor' AS source_table,
        ROW_NUMBER() OVER (
            PARTITION BY p.stay_id, p.charttime
            ORDER BY ABS(DATETIME_DIFF(p.charttime, f.charttime, MINUTE)) ASC
        ) AS rn
    FROM `mimic-study-498508.non_traumatic_sah_study.pao2_0_48h` p
    INNER JOIN `mimic-study-498508.non_traumatic_sah_study.blood_gas_fio2_cleaned_0_48h` f
        ON p.stay_id = f.stay_id
       AND f.fio2 IS NOT NULL
       AND f.charttime BETWEEN DATETIME_SUB(p.charttime, INTERVAL 2 HOUR)
                           AND DATETIME_ADD(p.charttime, INTERVAL 2 HOUR)
),
all_pao2_fio2 AS (
    SELECT
        subject_id,
        hadm_id,
        stay_id,
        pao2_time,
        fio2_time,
        pao2,
        fio2,
        pao2_fio2_ratio,
        time_diff_minutes,
        source_table
    FROM derived_bg
    UNION ALL
    SELECT
        subject_id,
        hadm_id,
        stay_id,
        pao2_time,
        fio2_time,
        pao2,
        fio2,
        pao2_fio2_ratio,
        time_diff_minutes,
        source_table
    FROM matched_raw
    WHERE rn = 1
      AND pao2_fio2_ratio BETWEEN 50 AND 700
)
SELECT * EXCEPT(source_priority, rn)
FROM (
    SELECT
        *,
        CASE
            WHEN source_table = 'mimiciv_3_1_derived.bg' THEN 1
            ELSE 2
        END AS source_priority,
        ROW_NUMBER() OVER (
            PARTITION BY stay_id, pao2_time
            ORDER BY
                CASE
                    WHEN source_table = 'mimiciv_3_1_derived.bg' THEN 1
                    ELSE 2
                END
        ) AS rn
    FROM all_pao2_fio2
)
WHERE rn = 1;

-- 验证：PaO2/FiO2 覆盖率、范围和匹配时间差。
SELECT
    COUNT(*) AS matched_rows,
    COUNT(DISTINCT stay_id) AS stays_with_pao2_fio2,
    MIN(pao2_fio2_ratio) AS min_pao2_fio2,
    MAX(pao2_fio2_ratio) AS max_pao2_fio2,
    MAX(time_diff_minutes) AS max_time_diff_minutes
FROM `mimic-study-498508.non_traumatic_sah_study.pao2_fio2_0_48h`;

-- 目的：用 SpO2 前后 2 小时内最近 FiO2 计算 SpO2/FiO2。
-- 原因：SpO2 与 FiO2 不一定同一时间记录；当 PaO2/FiO2 不可用时，SpO2/FiO2 作为兜底氧合指标。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.spo2_fio2_0_48h` AS
WITH matched AS (
    SELECT
        s.subject_id,
        s.hadm_id,
        s.stay_id,
        s.charttime AS spo2_time,
        f.charttime AS fio2_time,
        s.spo2,
        f.fio2,
        s.spo2 / NULLIF(f.fio2, 0) AS spo2_fio2_ratio,
        ABS(DATETIME_DIFF(s.charttime, f.charttime, MINUTE)) AS time_diff_minutes,
        ROW_NUMBER() OVER (
            PARTITION BY s.stay_id, s.charttime
            ORDER BY ABS(DATETIME_DIFF(s.charttime, f.charttime, MINUTE)) ASC
        ) AS rn
    FROM `mimic-study-498508.non_traumatic_sah_study.spo2_0_48h` s
    INNER JOIN `mimic-study-498508.non_traumatic_sah_study.fio2_cleaned_0_48h` f
        ON s.stay_id = f.stay_id
       AND f.fio2 IS NOT NULL
       AND f.charttime BETWEEN DATETIME_SUB(s.charttime, INTERVAL 2 HOUR)
                           AND DATETIME_ADD(s.charttime, INTERVAL 2 HOUR)
)
SELECT *
FROM matched
WHERE rn = 1
  AND spo2_fio2_ratio BETWEEN 50 AND 500;

-- 验证：SpO2/FiO2 覆盖率、范围和匹配时间差。
SELECT
    COUNT(*) AS matched_rows,
    COUNT(DISTINCT stay_id) AS stays_with_spo2_fio2,
    MIN(spo2_fio2_ratio) AS min_spo2_fio2,
    MAX(spo2_fio2_ratio) AS max_spo2_fio2,
    MAX(time_diff_minutes) AS max_time_diff_minutes
FROM `mimic-study-498508.non_traumatic_sah_study.spo2_fio2_0_48h`;

-- 目的：生成最终氧合明细表，PaO2/FiO2 优先，SpO2/FiO2 兜底。
-- 原因：保留血气/FiO2 氧合比值用于描述和敏感性分析；主聚类使用低缺失 SpO2。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.oxygenation_0_48h` AS
SELECT
    subject_id,
    hadm_id,
    stay_id,
    pao2_time AS charttime,
    pao2_fio2_ratio AS oxygenation_ratio,
    'pao2_fio2' AS oxygenation_source,
    fio2,
    time_diff_minutes
FROM `mimic-study-498508.non_traumatic_sah_study.pao2_fio2_0_48h`
UNION ALL
SELECT
    sf.subject_id,
    sf.hadm_id,
    sf.stay_id,
    sf.spo2_time AS charttime,
    sf.spo2_fio2_ratio AS oxygenation_ratio,
    'spo2_fio2' AS oxygenation_source,
    sf.fio2,
    sf.time_diff_minutes
FROM `mimic-study-498508.non_traumatic_sah_study.spo2_fio2_0_48h` sf
WHERE NOT EXISTS (
    SELECT 1
    FROM `mimic-study-498508.non_traumatic_sah_study.pao2_fio2_0_48h` pf
    WHERE pf.stay_id = sf.stay_id
);

-- 验证：氧合变量各来源覆盖率。
SELECT
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.pao2_0_48h`) AS stays_with_pao2,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.blood_gas_fio2_cleaned_0_48h` WHERE fio2 IS NOT NULL) AS stays_with_blood_gas_fio2,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.pao2_fio2_0_48h`) AS stays_with_pao2_fio2,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.spo2_0_48h`) AS stays_with_spo2,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.fio2_cleaned_0_48h` WHERE fio2 IS NOT NULL) AS stays_with_charted_fio2,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.spo2_fio2_0_48h`) AS stays_with_spo2_fio2,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.non_traumatic_sah_study.oxygenation_0_48h`) AS stays_with_final_oxygenation;

-- -----------------------------------------------------------------------------
-- 5. 0-48h 核心特征聚合宽表
-- -----------------------------------------------------------------------------

-- 目的：将明细指标聚合为一行一个 stay 的 0-48h 特征宽表。
-- 原因：K-means 聚类输入需要固定维度的样本特征矩阵。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.analysis_features_48h` AS
WITH hb AS (
    SELECT
        h.stay_id,
        MIN(h.hb) AS hb_min_48h_all,
        MIN(CASE
            WHEN rf.first_rbc_time_48h IS NULL OR h.charttime < rf.first_rbc_time_48h THEN h.hb
            ELSE NULL
        END) AS hb_min_48h_pre_transfusion,
        COUNT(*) AS hb_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.hb_0_48h` h
    LEFT JOIN `mimic-study-498508.non_traumatic_sah_study.rbc_transfusion_flags` rf
        ON h.stay_id = rf.stay_id
    GROUP BY h.stay_id
),
epvs AS (
    SELECT
        stay_id,
        ARRAY_AGG(epvs ORDER BY charttime ASC LIMIT 1)[OFFSET(0)] AS epvs_first_48h,
        AVG(epvs) AS epvs_mean_48h,
        MIN(epvs) AS epvs_min_48h,
        MAX(epvs) AS epvs_max_48h,
        COUNT(*) AS epvs_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.epvs_0_48h`
    GROUP BY stay_id
),
gcs AS (
    SELECT
        stay_id,
        MIN(gcs_total) AS gcs_min_48h,
        CASE
            WHEN MIN(gcs_total) BETWEEN 3 AND 8 THEN 3
            WHEN MIN(gcs_total) BETWEEN 9 AND 12 THEN 2
            WHEN MIN(gcs_total) BETWEEN 13 AND 15 THEN 1
            ELSE NULL
        END AS gcs_grade_min_48h,
        MIN(gcs_motor) AS gcs_motor_min_48h,
        CASE
            WHEN MIN(gcs_total) = 15 THEN 1
            WHEN MIN(gcs_total) BETWEEN 13 AND 14 THEN 2
            WHEN MIN(gcs_total) BETWEEN 7 AND 12 THEN 4
            WHEN MIN(gcs_total) BETWEEN 3 AND 6 THEN 5
            ELSE NULL
        END AS wfns_gcs_grade_min_48h,
        COUNTIF(gcs_total IS NOT NULL) AS gcs_measurement_count,
        COUNTIF(gcs_motor IS NOT NULL) AS gcs_motor_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.gcs_0_48h`
    GROUP BY stay_id
),
map_agg AS (
    SELECT
        stay_id,
        MIN(map_value) AS map_min_48h,
        AVG(map_value) AS map_mean_48h,
        COUNT(*) AS map_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.map_0_48h`
    GROUP BY stay_id
),
si AS (
    SELECT
        stay_id,
        MAX(shock_index) AS shock_index_max_48h,
        AVG(shock_index) AS shock_index_mean_48h,
        COUNT(*) AS shock_index_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.shock_index_0_48h`
    GROUP BY stay_id
),
lactate AS (
    SELECT
        stay_id,
        MAX(lactate) AS lactate_max_48h,
        AVG(lactate) AS lactate_mean_48h,
        COUNT(*) AS lactate_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.lactate_0_48h`
    GROUP BY stay_id
),
oxygen AS (
    SELECT
        stay_id,
        MIN(oxygenation_ratio) AS oxygenation_min_48h,
        AVG(oxygenation_ratio) AS oxygenation_mean_48h,
        COUNT(*) AS oxygenation_measurement_count,
        STRING_AGG(DISTINCT oxygenation_source, ', ' ORDER BY oxygenation_source) AS oxygenation_source_48h
    FROM `mimic-study-498508.non_traumatic_sah_study.oxygenation_0_48h`
    GROUP BY stay_id
),
pao2_fio2 AS (
    SELECT
        stay_id,
        MIN(pao2_fio2_ratio) AS pao2_fio2_min_48h,
        AVG(pao2_fio2_ratio) AS pao2_fio2_mean_48h,
        COUNT(*) AS pao2_fio2_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.pao2_fio2_0_48h`
    GROUP BY stay_id
),
spo2_fio2 AS (
    SELECT
        stay_id,
        MIN(spo2_fio2_ratio) AS spo2_fio2_min_48h,
        AVG(spo2_fio2_ratio) AS spo2_fio2_mean_48h,
        COUNT(*) AS spo2_fio2_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.spo2_fio2_0_48h`
    GROUP BY stay_id
),
spo2 AS (
    SELECT
        stay_id,
        MIN(spo2) AS spo2_min_48h,
        AVG(spo2) AS spo2_mean_48h,
        COUNT(*) AS spo2_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.spo2_0_48h`
    GROUP BY stay_id
),
troponin AS (
    SELECT
        stay_id,
        MAX(troponin_value) AS troponin_peak_48h,
        COUNT(*) AS troponin_measurement_count,
        STRING_AGG(DISTINCT troponin_label, ', ' ORDER BY troponin_label) AS troponin_labels_48h,
        STRING_AGG(DISTINCT valueuom, ', ' ORDER BY valueuom) AS troponin_units_48h
    FROM `mimic-study-498508.non_traumatic_sah_study.troponin_0_48h`
    GROUP BY stay_id
),
creatinine AS (
    SELECT
        stay_id,
        MAX(creatinine) AS creatinine_max_48h,
        AVG(creatinine) AS creatinine_mean_48h,
        COUNT(*) AS creatinine_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.creatinine_0_48h`
    GROUP BY stay_id
),
platelet AS (
    SELECT
        stay_id,
        MIN(platelet) AS platelet_min_48h,
        AVG(platelet) AS platelet_mean_48h,
        COUNT(*) AS platelet_measurement_count
    FROM `mimic-study-498508.non_traumatic_sah_study.platelet_0_48h`
    GROUP BY stay_id
)
SELECT
    c.subject_id,
    c.hadm_id,
    c.stay_id,
    c.age,
    c.gender,
    c.race,
    c.admission_type,
    c.insurance,
    c.nsah_evidence_level,
    c.has_aneurysm_dx,
    c.has_aneurysm_procedure,
    c.icu_intime,
    c.icu_outtime,
    c.icu_los_hours,
    c.icu_los_hours / 24.0 AS icu_los_days,
    c.hospital_los_days,
    c.hospital_expire_flag AS hospital_mortality,
    c.icu_mortality,
    rf.any_rbc_transfusion_48h,
    rf.massive_transfusion_24h,
    rf.first_rbc_time_48h,
    rf.rbc_events_24h,
    rf.rbc_events_48h,
    rf.rbc_units_24h,
    rf.rbc_units_48h,
    hb.hb_min_48h_all,
    hb.hb_min_48h_pre_transfusion,
    epvs.epvs_first_48h,
    epvs.epvs_mean_48h,
    epvs.epvs_min_48h,
    epvs.epvs_max_48h,
    gcs.gcs_min_48h,
    gcs.gcs_grade_min_48h,
    gcs.gcs_motor_min_48h,
    gcs.wfns_gcs_grade_min_48h,
    CAST(NULL AS FLOAT64) AS sapsiii_24h,
    CAST(NULL AS FLOAT64) AS sofa_24h,
    map_agg.map_min_48h,
    map_agg.map_mean_48h,
    si.shock_index_max_48h,
    si.shock_index_mean_48h,
    lactate.lactate_max_48h,
    lactate.lactate_mean_48h,
    oxygen.oxygenation_min_48h,
    oxygen.oxygenation_mean_48h,
    oxygen.oxygenation_source_48h,
    pao2_fio2.pao2_fio2_min_48h,
    pao2_fio2.pao2_fio2_mean_48h,
    spo2_fio2.spo2_fio2_min_48h,
    spo2_fio2.spo2_fio2_mean_48h,
    spo2.spo2_min_48h,
    spo2.spo2_mean_48h,
    troponin.troponin_peak_48h,
    troponin.troponin_labels_48h,
    troponin.troponin_units_48h,
    creatinine.creatinine_max_48h,
    creatinine.creatinine_mean_48h,
    platelet.platelet_min_48h,
    platelet.platelet_mean_48h,
    CASE WHEN hb.hb_min_48h_all < 10 THEN 1 ELSE 0 END AS early_anemia_all,
    CASE WHEN hb.hb_min_48h_pre_transfusion < 10 THEN 1 ELSE 0 END AS early_anemia_pre_transfusion,
    CASE WHEN rf.first_rbc_time_48h IS NOT NULL AND hb.hb_min_48h_all IS NOT NULL THEN 1 ELSE 0 END AS has_hb_and_rbc_48h,
    (
        IF(hb.hb_min_48h_all IS NULL, 1, 0)
      + IF(gcs.gcs_min_48h IS NULL, 1, 0)
      + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
      + IF(map_agg.map_min_48h IS NULL, 1, 0)
      + IF(si.shock_index_max_48h IS NULL, 1, 0)
      + IF(spo2.spo2_min_48h IS NULL, 1, 0)
      + IF(creatinine.creatinine_max_48h IS NULL, 1, 0)
      + IF(platelet.platelet_min_48h IS NULL, 1, 0)
    ) AS core_feature_missing_count,
    hb.hb_measurement_count,
    epvs.epvs_measurement_count,
    gcs.gcs_measurement_count,
    gcs.gcs_motor_measurement_count,
    map_agg.map_measurement_count,
    si.shock_index_measurement_count,
    lactate.lactate_measurement_count,
    oxygen.oxygenation_measurement_count,
    pao2_fio2.pao2_fio2_measurement_count,
    spo2_fio2.spo2_fio2_measurement_count,
    spo2.spo2_measurement_count,
    troponin.troponin_measurement_count,
    creatinine.creatinine_measurement_count,
    platelet.platelet_measurement_count
FROM `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort` c
LEFT JOIN `mimic-study-498508.non_traumatic_sah_study.rbc_transfusion_flags` rf
    ON c.stay_id = rf.stay_id
LEFT JOIN hb
    ON c.stay_id = hb.stay_id
LEFT JOIN epvs
    ON c.stay_id = epvs.stay_id
LEFT JOIN gcs
    ON c.stay_id = gcs.stay_id
LEFT JOIN map_agg
    ON c.stay_id = map_agg.stay_id
LEFT JOIN si
    ON c.stay_id = si.stay_id
LEFT JOIN lactate
    ON c.stay_id = lactate.stay_id
LEFT JOIN oxygen
    ON c.stay_id = oxygen.stay_id
LEFT JOIN pao2_fio2
    ON c.stay_id = pao2_fio2.stay_id
LEFT JOIN spo2_fio2
    ON c.stay_id = spo2_fio2.stay_id
LEFT JOIN spo2
    ON c.stay_id = spo2.stay_id
LEFT JOIN troponin
    ON c.stay_id = troponin.stay_id
LEFT JOIN creatinine
    ON c.stay_id = creatinine.stay_id
LEFT JOIN platelet
    ON c.stay_id = platelet.stay_id;

-- 验证：检查核心变量覆盖率、缺失计数和主分析可纳入样本数。
SELECT
    COUNT(*) AS total_rows,
    COUNTIF(hb_min_48h_all IS NOT NULL) AS hb_nonmissing,
    COUNTIF(epvs_mean_48h IS NOT NULL) AS epvs_nonmissing,
    COUNTIF(gcs_min_48h IS NOT NULL) AS gcs_nonmissing,
    COUNTIF(gcs_grade_min_48h IS NOT NULL) AS gcs_grade_nonmissing,
    COUNTIF(gcs_motor_min_48h IS NOT NULL) AS gcs_motor_nonmissing,
    COUNTIF(map_min_48h IS NOT NULL) AS map_nonmissing,
    COUNTIF(shock_index_max_48h IS NOT NULL) AS shock_index_nonmissing,
    COUNTIF(lactate_max_48h IS NOT NULL) AS lactate_nonmissing,
    COUNTIF(oxygenation_min_48h IS NOT NULL) AS oxygenation_nonmissing,
    COUNTIF(pao2_fio2_min_48h IS NOT NULL) AS pao2_fio2_nonmissing,
    COUNTIF(spo2_fio2_min_48h IS NOT NULL) AS spo2_fio2_only_nonmissing,
    COUNTIF(spo2_min_48h IS NOT NULL) AS spo2_nonmissing,
    COUNTIF(troponin_peak_48h IS NOT NULL) AS troponin_nonmissing,
    COUNTIF(creatinine_max_48h IS NOT NULL) AS creatinine_nonmissing,
    COUNTIF(platelet_min_48h IS NOT NULL) AS platelet_nonmissing,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0) AS eligible_primary_analysis_rows,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0 AND icu_los_hours >= 48) AS eligible_48h_los_sensitivity_rows,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0 AND any_rbc_transfusion_48h = 0) AS eligible_no_rbc_sensitivity_rows
FROM `mimic-study-498508.non_traumatic_sah_study.analysis_features_48h`;

SELECT
    core_feature_missing_count,
    COUNT(*) AS rows_count
FROM `mimic-study-498508.non_traumatic_sah_study.analysis_features_48h`
GROUP BY core_feature_missing_count
ORDER BY core_feature_missing_count;

-- 目的：生成主分析最终宽表。
-- 原因：Python 聚类和结局分析直接读取该表；仍保留敏感性分析所需标记。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` AS
SELECT
    *,
    CASE
        WHEN core_feature_missing_count <= 2
         AND massive_transfusion_24h = 0 THEN 1
        ELSE 0
    END AS eligible_primary_analysis,
    CASE
        WHEN core_feature_missing_count <= 2
         AND massive_transfusion_24h = 0
         AND icu_los_hours >= 48 THEN 1
        ELSE 0
    END AS eligible_sensitivity_48h_los,
    CASE
        WHEN core_feature_missing_count <= 2
         AND massive_transfusion_24h = 0
         AND any_rbc_transfusion_48h = 0 THEN 1
        ELSE 0
    END AS eligible_no_transfusion_sensitivity
FROM `mimic-study-498508.non_traumatic_sah_study.analysis_features_48h`;

-- 验证：最终宽表规模、主分析样本量、贫血比例和死亡率。
SELECT
    COUNT(*) AS all_feature_rows,
    COUNTIF(eligible_primary_analysis = 1) AS primary_analysis_rows,
    COUNTIF(eligible_sensitivity_48h_los = 1) AS sensitivity_48h_los_rows,
    COUNTIF(eligible_no_transfusion_sensitivity = 1) AS no_transfusion_sensitivity_rows,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(hospital_mortality AS FLOAT64) ELSE NULL END) AS primary_hospital_mortality_rate,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(early_anemia_all AS FLOAT64) ELSE NULL END) AS primary_early_anemia_rate,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(any_rbc_transfusion_48h AS FLOAT64) ELSE NULL END) AS primary_any_rbc_rate
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`;

-- 验证：主分析样本中 8 个低缺失主聚类变量范围；高缺失血气变量仅作敏感性字段检查。
SELECT
    MIN(hb_min_48h_all) AS min_hb_min_48h,
    MAX(hb_min_48h_all) AS max_hb_min_48h,
    MIN(gcs_min_48h) AS min_gcs_min_48h,
    MAX(gcs_min_48h) AS max_gcs_min_48h,
    MIN(gcs_motor_min_48h) AS min_gcs_motor_min_48h,
    MAX(gcs_motor_min_48h) AS max_gcs_motor_min_48h,
    MIN(gcs_grade_min_48h) AS min_gcs_grade_min_48h_descriptive,
    MAX(gcs_grade_min_48h) AS max_gcs_grade_min_48h_descriptive,
    MIN(map_min_48h) AS min_map_min_48h,
    MAX(map_min_48h) AS max_map_min_48h,
    MIN(shock_index_max_48h) AS min_shock_index_max_48h,
    MAX(shock_index_max_48h) AS max_shock_index_max_48h,
    MIN(spo2_min_48h) AS min_spo2_min_48h,
    MAX(spo2_min_48h) AS max_spo2_min_48h,
    MIN(epvs_mean_48h) AS min_epvs_mean_48h_candidate,
    MAX(epvs_mean_48h) AS max_epvs_mean_48h_candidate,
    MIN(troponin_peak_48h) AS min_troponin_peak_48h_candidate,
    MAX(troponin_peak_48h) AS max_troponin_peak_48h_candidate,
    MIN(lactate_max_48h) AS min_lactate_max_48h,
    MAX(lactate_max_48h) AS max_lactate_max_48h,
    MIN(oxygenation_min_48h) AS min_oxygenation_min_48h,
    MAX(oxygenation_min_48h) AS max_oxygenation_min_48h,
    MIN(pao2_fio2_min_48h) AS min_pao2_fio2_min_48h,
    MAX(pao2_fio2_min_48h) AS max_pao2_fio2_min_48h,
    MIN(spo2_fio2_min_48h) AS min_spo2_fio2_min_48h,
    MAX(spo2_fio2_min_48h) AS max_spo2_fio2_min_48h,
    MIN(creatinine_max_48h) AS min_creatinine_max_48h,
    MAX(creatinine_max_48h) AS max_creatinine_max_48h,
    MIN(platelet_min_48h) AS min_platelet_min_48h,
    MAX(platelet_min_48h) AS max_platelet_min_48h
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
WHERE eligible_primary_analysis = 1;

-- -----------------------------------------------------------------------------
-- 6. Flowchart 与建模前可行性检查
-- -----------------------------------------------------------------------------

-- 目的：生成 cohort flowchart 计数表。
-- 原因：论文需要逐步报告样本筛选过程，也方便发现样本损失最大的步骤。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.cohort_flowchart_counts` AS
SELECT '01_source_sah_admissions' AS step, COUNT(*) AS rows_count, COUNT(DISTINCT subject_id) AS patients, COUNT(DISTINCT hadm_id) AS admissions
FROM `mimic-study-498508.non_traumatic_sah_study.source_sah_admissions`
UNION ALL
SELECT '02_adult_source_sah', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.source_sah_admissions`
WHERE is_adult = 1
UNION ALL
SELECT '03_adult_nontraumatic_sah_no_extra_aneurysm_required', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.confirmed_nsah_admissions`
UNION ALL
SELECT '04_first_icu_nsah_stays', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.first_icu_nsah_stays`
UNION ALL
SELECT '05_icu_los_ge_24h', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.eligible_icu_cohort`
UNION ALL
SELECT '06_core_missing_le_2', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
WHERE core_feature_missing_count <= 2
UNION ALL
SELECT '07_primary_analysis_no_massive_transfusion', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
WHERE eligible_primary_analysis = 1
UNION ALL
SELECT '08_sensitivity_icu_los_ge_48h', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
WHERE eligible_sensitivity_48h_los = 1
UNION ALL
SELECT '09_sensitivity_no_rbc_48h', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
WHERE eligible_no_transfusion_sensitivity = 1;

-- 验证：查看 flowchart 计数。
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.cohort_flowchart_counts`
ORDER BY step;

-- 目的：生成主分析样本的变量缺失率汇总。
-- 原因：Python 插补和建模前需要确认各变量缺失程度。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.feature_missingness_summary` AS
SELECT 'hb_min_48h_all' AS feature, COUNTIF(hb_min_48h_all IS NULL) AS missing_n, COUNT(*) AS total_n, COUNTIF(hb_min_48h_all IS NULL) / COUNT(*) AS missing_rate
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'epvs_mean_48h_candidate', COUNTIF(epvs_mean_48h IS NULL), COUNT(*), COUNTIF(epvs_mean_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'gcs_min_48h', COUNTIF(gcs_min_48h IS NULL), COUNT(*), COUNTIF(gcs_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'gcs_grade_min_48h_descriptive', COUNTIF(gcs_grade_min_48h IS NULL), COUNT(*), COUNTIF(gcs_grade_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'gcs_motor_min_48h', COUNTIF(gcs_motor_min_48h IS NULL), COUNT(*), COUNTIF(gcs_motor_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'map_min_48h', COUNTIF(map_min_48h IS NULL), COUNT(*), COUNTIF(map_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'shock_index_max_48h', COUNTIF(shock_index_max_48h IS NULL), COUNT(*), COUNTIF(shock_index_max_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'spo2_min_48h', COUNTIF(spo2_min_48h IS NULL), COUNT(*), COUNTIF(spo2_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'troponin_peak_48h_candidate', COUNTIF(troponin_peak_48h IS NULL), COUNT(*), COUNTIF(troponin_peak_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'lactate_max_48h_sensitivity', COUNTIF(lactate_max_48h IS NULL), COUNT(*), COUNTIF(lactate_max_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'oxygenation_min_48h_sensitivity', COUNTIF(oxygenation_min_48h IS NULL), COUNT(*), COUNTIF(oxygenation_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'creatinine_max_48h', COUNTIF(creatinine_max_48h IS NULL), COUNT(*), COUNTIF(creatinine_max_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'platelet_min_48h', COUNTIF(platelet_min_48h IS NULL), COUNT(*), COUNTIF(platelet_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1;

-- 验证：查看缺失率汇总。
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.feature_missingness_summary`
ORDER BY missing_rate DESC;

-- 目的：单独汇总氧合变量不同来源的覆盖率。
-- 原因：最终氧合变量混合了 PaO2/FiO2 和 SpO2/FiO2，需要确认覆盖率提升来自哪里。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.oxygenation_source_missingness_summary` AS
SELECT 'oxygenation_min_48h' AS feature, COUNTIF(oxygenation_min_48h IS NULL) AS missing_n, COUNT(*) AS total_n, COUNTIF(oxygenation_min_48h IS NULL) / COUNT(*) AS missing_rate
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'pao2_fio2_min_48h', COUNTIF(pao2_fio2_min_48h IS NULL), COUNT(*), COUNTIF(pao2_fio2_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'spo2_fio2_min_48h', COUNTIF(spo2_fio2_min_48h IS NULL), COUNT(*), COUNTIF(spo2_fio2_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` WHERE eligible_primary_analysis = 1;

-- 验证：查看氧合来源缺失率。
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.oxygenation_source_missingness_summary`
ORDER BY missing_rate DESC;

-- 目的：输出建模前 feasibility 基线表框架。
-- 原因：聚类完成后应按 phenotype 补充 N、死亡、贫血、贫血死亡等计数，判断分层回归是否稳定。
CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.pre_clustering_feasibility_summary` AS
SELECT
    eligible_primary_analysis,
    COUNT(*) AS n,
    COUNTIF(hospital_mortality = 1) AS deaths,
    COUNTIF(early_anemia_all = 1) AS anemia_n,
    COUNTIF(early_anemia_all = 0) AS non_anemia_n,
    COUNTIF(early_anemia_all = 1 AND hospital_mortality = 1) AS anemia_deaths,
    COUNTIF(early_anemia_all = 0 AND hospital_mortality = 1) AS non_anemia_deaths
FROM `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h`
GROUP BY eligible_primary_analysis;

-- 验证：查看聚类前总体可行性计数。
SELECT *
FROM `mimic-study-498508.non_traumatic_sah_study.pre_clustering_feasibility_summary`
ORDER BY eligible_primary_analysis DESC;
