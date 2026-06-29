-- aSAH 早期多模态生理表型 cohort 构建脚本
-- 数据源：MIMIC-IV 3.1 BigQuery
-- 目标位置：mimic-study-498508.ash_study
--
-- 设计原则：
-- 1. 先宽后严：先保留候选人群和筛选标记，再生成主分析 cohort。
-- 2. 时间锚点：首次 ICU 入科时间 icu_intime。
-- 3. 主窗口：ICU 入科后 0-48 小时；敏感性窗口可复用明细表改成 0-24 小时。
-- 4. 聚类变量：Hb、GCS motor、MAP、shock index、lactate、SpO2/FiO2、creatinine、platelet。
-- 5. 每个关键步骤后都附带验证查询，便于检查样本量、唯一性、覆盖率和异常值。

-- 目的：创建本研究专用数据集。
-- 原因：所有 cohort 中间表和最终宽表统一存储，方便复现、排查和清理。
CREATE SCHEMA IF NOT EXISTS `mimic-study-498508.ash_study`;

-- 验证：确认目标 project 和 dataset。
SELECT
    'mimic-study-498508' AS project_id,
    'ash_study' AS dataset_id,
    'aSAH 早期多模态生理表型研究' AS study_note;

-- -----------------------------------------------------------------------------
-- 1. 诊断与操作证据：建立 SAH/aSAH 候选住院
-- -----------------------------------------------------------------------------

-- 目的：提取 SAH 诊断、动脉瘤诊断和创伤性 SAH 诊断标记。
-- 原因：单独 SAH ICD 不能保证是动脉瘤性 SAH，需要逐层保留诊断证据。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.dx_sah_flags` AS
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
FROM `mimic-study-498508.ash_study.dx_sah_flags`;

-- 目的：从操作代码字典中识别 clipping/coiling/endovascular embolization 等动脉瘤处置候选。
-- 原因：处置证据可作为更高特异性的 aSAH 识别标准和敏感性分析依据。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.aneurysm_procedure_flags` AS
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
FROM `mimic-study-498508.ash_study.aneurysm_procedure_flags`;

SELECT *
FROM `mimic-study-498508.ash_study.aneurysm_procedure_flags`
ORDER BY subject_id, hadm_id
LIMIT 10;

-- 目的：建立宽松 SAH/aSAH 候选住院表，并保留诊断层级。
-- 原因：后续 flowchart 和敏感性分析需要知道每个住院满足哪一档 aSAH 定义。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.source_sah_admissions` AS
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
    END AS asah_evidence_level,
    CASE WHEN p.anchor_age >= 18 THEN 1 ELSE 0 END AS is_adult
FROM `physionet-data.mimiciv_3_1_hosp.admissions` a
INNER JOIN `physionet-data.mimiciv_3_1_hosp.patients` p
    ON a.subject_id = p.subject_id
INNER JOIN `mimic-study-498508.ash_study.dx_sah_flags` dx
    ON a.subject_id = dx.subject_id
   AND a.hadm_id = dx.hadm_id
LEFT JOIN `mimic-study-498508.ash_study.aneurysm_procedure_flags` proc
    ON a.subject_id = proc.subject_id
   AND a.hadm_id = proc.hadm_id
WHERE COALESCE(dx.has_sah_dx, 0) = 1;

-- 验证：检查 SAH 候选住院数量、成人比例和 aSAH 证据层级分布。
SELECT
    COUNT(*) AS source_sah_rows,
    COUNT(DISTINCT subject_id) AS source_sah_patients,
    COUNT(DISTINCT hadm_id) AS source_sah_admissions,
    COUNTIF(is_adult = 1) AS adult_admissions,
    COUNTIF(asah_evidence_level >= 2) AS strict_asah_admissions,
    COUNTIF(asah_evidence_level = 3) AS procedure_confirmed_admissions,
    COUNTIF(has_traumatic_sah_dx = 1) AS traumatic_sah_flagged
FROM `mimic-study-498508.ash_study.source_sah_admissions`;

SELECT
    asah_evidence_level,
    COUNT(*) AS admissions
FROM `mimic-study-498508.ash_study.source_sah_admissions`
GROUP BY asah_evidence_level
ORDER BY asah_evidence_level;

-- 目的：生成主分析候选 aSAH 住院。
-- 原因：主分析优先使用 SAH + 动脉瘤诊断或处置证据，排除明显创伤性 SAH，并限定成人。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.confirmed_asah_admissions` AS
SELECT *
FROM `mimic-study-498508.ash_study.source_sah_admissions`
WHERE is_adult = 1
  AND asah_evidence_level >= 2
  AND has_traumatic_sah_dx = 0;

-- 验证：检查主分析候选 aSAH 住院规模和唯一性。
SELECT
    COUNT(*) AS confirmed_rows,
    COUNT(DISTINCT subject_id) AS confirmed_patients,
    COUNT(DISTINCT hadm_id) AS confirmed_admissions,
    COUNT(*) - COUNT(DISTINCT CONCAT(CAST(subject_id AS STRING), '-', CAST(hadm_id AS STRING))) AS duplicate_subject_hadm_rows,
    AVG(CAST(hospital_expire_flag AS FLOAT64)) AS hospital_mortality_rate
FROM `mimic-study-498508.ash_study.confirmed_asah_admissions`;

-- -----------------------------------------------------------------------------
-- 2. 首次 ICU stay 与基础 eligible cohort
-- -----------------------------------------------------------------------------

-- 目的：为每次 aSAH 住院选择首次 ICU stay。
-- 原因：首次 ICU stay 最接近入院早期状态，避免重复 ICU stay 和治疗后状态污染。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.first_icu_asah_stays` AS
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
        ca.asah_evidence_level,
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
    FROM `mimic-study-498508.ash_study.confirmed_asah_admissions` ca
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
FROM `mimic-study-498508.ash_study.first_icu_asah_stays`;

-- 验证：确认每个 stay_id 只出现一次。
SELECT
    stay_id,
    COUNT(*) AS row_count
FROM `mimic-study-498508.ash_study.first_icu_asah_stays`
GROUP BY stay_id
HAVING COUNT(*) > 1;

-- 目的：生成基础 eligible cohort，暂时只限定 ICU stay >=24h。
-- 原因：核心特征缺失、输血等条件应在宽表中保留标记后再筛选，避免过早删除样本。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.eligible_icu_cohort` AS
SELECT *
FROM `mimic-study-498508.ash_study.first_icu_asah_stays`
WHERE icu_los_ge_24h = 1;

-- 验证：检查基础 eligible cohort 规模和结局。
SELECT
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT subject_id) AS eligible_patients,
    COUNT(DISTINCT stay_id) AS eligible_stays,
    AVG(CAST(hospital_expire_flag AS FLOAT64)) AS hospital_mortality_rate,
    AVG(CAST(icu_mortality AS FLOAT64)) AS icu_mortality_rate,
    AVG(icu_los_hours) / 24.0 AS mean_icu_los_days
FROM `mimic-study-498508.ash_study.eligible_icu_cohort`;

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
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.rbc_transfusion_0_48h` AS
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
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
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
FROM `mimic-study-498508.ash_study.rbc_transfusion_0_48h`;

-- 目的：按 stay 汇总 0-24h 和 0-48h 输血标记。
-- 原因：主分析排除大量输血，敏感性分析可排除所有输血患者。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.rbc_transfusion_flags` AS
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
FROM `mimic-study-498508.ash_study.eligible_icu_cohort` c
LEFT JOIN `mimic-study-498508.ash_study.rbc_transfusion_0_48h` t
    ON c.stay_id = t.stay_id
GROUP BY c.subject_id, c.hadm_id, c.stay_id;

-- 验证：检查普通输血和大量输血标记。
SELECT
    COUNT(*) AS cohort_stays,
    COUNTIF(any_rbc_transfusion_48h = 1) AS stays_with_any_rbc_48h,
    COUNTIF(massive_transfusion_24h = 1) AS stays_with_massive_rbc_24h,
    MIN(rbc_events_48h) AS min_rbc_events_48h,
    MAX(rbc_events_48h) AS max_rbc_events_48h
FROM `mimic-study-498508.ash_study.rbc_transfusion_flags`;

-- -----------------------------------------------------------------------------
-- 4. 0-48h 核心生理指标明细表
-- -----------------------------------------------------------------------------

-- 目的：提取 0-48h Hb 明细，并标记是否发生在首次 RBC 输血前。
-- 原因：Hb 是贫血定义和聚类变量，输血后 Hb 可能被治疗改变。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.hb_0_48h` AS
SELECT
    le.subject_id,
    le.hadm_id,
    c.stay_id,
    le.charttime,
    DATETIME_DIFF(le.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    le.itemid AS source_itemid,
    le.valuenum AS hb
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON le.subject_id = c.subject_id
   AND le.hadm_id = c.hadm_id
WHERE le.itemid = 51222
  AND le.valuenum > 3
  AND le.valuenum < 25
  AND le.charttime >= c.icu_intime
  AND le.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：Hb 覆盖率、范围和窗口。
SELECT
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(hb) AS min_hb,
    APPROX_QUANTILES(hb, 4)[OFFSET(2)] AS median_hb,
    MAX(hb) AS max_hb,
    MIN(hours_from_icu_intime) AS min_hours,
    MAX(hours_from_icu_intime) AS max_hours
FROM `mimic-study-498508.ash_study.hb_0_48h`;

-- 目的：提取 0-48h GCS motor 明细。
-- 原因：GCS motor 代表早期神经功能，但解释时需考虑镇静/插管影响。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.gcs_motor_0_48h` AS
SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime,
    DATETIME_DIFF(ce.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    ce.itemid AS source_itemid,
    ce.valuenum AS gcs_motor
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON ce.stay_id = c.stay_id
WHERE ce.itemid = 220739
  AND ce.valuenum BETWEEN 1 AND 6
  AND ce.charttime >= c.icu_intime
  AND ce.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：GCS motor 覆盖率和范围。
SELECT
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(gcs_motor) AS min_gcs_motor,
    MAX(gcs_motor) AS max_gcs_motor
FROM `mimic-study-498508.ash_study.gcs_motor_0_48h`;

-- 目的：提取 0-48h MAP 明细。
-- 原因：最低 MAP 反映早期循环灌注最差状态。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.map_0_48h` AS
SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime,
    DATETIME_DIFF(ce.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    ce.itemid AS source_itemid,
    ce.valuenum AS map_value
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON ce.stay_id = c.stay_id
WHERE ce.itemid IN (220181, 225309)
  AND ce.valuenum BETWEEN 30 AND 200
  AND ce.charttime >= c.icu_intime
  AND ce.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：MAP 覆盖率和范围。
SELECT
    COUNT(*) AS measurements,
    COUNT(DISTINCT stay_id) AS stays_covered,
    MIN(map_value) AS min_map,
    MAX(map_value) AS max_map
FROM `mimic-study-498508.ash_study.map_0_48h`;

-- 目的：提取 0-48h 心率和收缩压明细。
-- 原因：shock index = HR / SBP，需要先分别清洗 HR 与 SBP。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.heart_rate_0_48h` AS
SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime,
    DATETIME_DIFF(ce.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    ce.itemid AS source_itemid,
    ce.valuenum AS heart_rate
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON ce.stay_id = c.stay_id
WHERE ce.itemid = 220045
  AND ce.valuenum BETWEEN 30 AND 220
  AND ce.charttime >= c.icu_intime
  AND ce.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.sbp_0_48h` AS
SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime,
    DATETIME_DIFF(ce.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    ce.itemid AS source_itemid,
    ce.valuenum AS sbp
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON ce.stay_id = c.stay_id
WHERE ce.itemid = 220179
  AND ce.valuenum BETWEEN 50 AND 260
  AND ce.charttime >= c.icu_intime
  AND ce.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：HR/SBP 覆盖率。
SELECT
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.ash_study.heart_rate_0_48h`) AS stays_with_hr,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.ash_study.sbp_0_48h`) AS stays_with_sbp,
    (SELECT COUNT(*) FROM `mimic-study-498508.ash_study.heart_rate_0_48h`) AS hr_measurements,
    (SELECT COUNT(*) FROM `mimic-study-498508.ash_study.sbp_0_48h`) AS sbp_measurements;

-- 目的：使用 HR 前后 30 分钟内最近 SBP 计算 shock index。
-- 原因：HR 和 SBP 不一定同一 charttime，近邻匹配比强制同一时刻覆盖率更高。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.shock_index_0_48h` AS
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
    FROM `mimic-study-498508.ash_study.heart_rate_0_48h` hr
    INNER JOIN `mimic-study-498508.ash_study.sbp_0_48h` sbp
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
FROM `mimic-study-498508.ash_study.shock_index_0_48h`;

-- 目的：提取 0-48h 乳酸、肌酐、血小板明细。
-- 原因：三者分别反映组织灌注、肾功能和凝血/炎症状态。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.lactate_0_48h` AS
SELECT
    le.subject_id,
    le.hadm_id,
    c.stay_id,
    le.charttime,
    DATETIME_DIFF(le.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    le.itemid AS source_itemid,
    le.valuenum AS lactate
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON le.subject_id = c.subject_id
   AND le.hadm_id = c.hadm_id
WHERE le.itemid = 50813
  AND le.valuenum > 0
  AND le.valuenum < 30
  AND le.charttime >= c.icu_intime
  AND le.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.creatinine_0_48h` AS
SELECT
    le.subject_id,
    le.hadm_id,
    c.stay_id,
    le.charttime,
    DATETIME_DIFF(le.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    le.itemid AS source_itemid,
    le.valuenum AS creatinine
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON le.subject_id = c.subject_id
   AND le.hadm_id = c.hadm_id
WHERE le.itemid = 50912
  AND le.valuenum BETWEEN 0.1 AND 20
  AND le.charttime >= c.icu_intime
  AND le.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.platelet_0_48h` AS
SELECT
    le.subject_id,
    le.hadm_id,
    c.stay_id,
    le.charttime,
    DATETIME_DIFF(le.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    le.itemid AS source_itemid,
    le.valuenum AS platelet
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON le.subject_id = c.subject_id
   AND le.hadm_id = c.hadm_id
WHERE le.itemid = 51265
  AND le.valuenum BETWEEN 10 AND 1000
  AND le.charttime >= c.icu_intime
  AND le.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

-- 验证：乳酸、肌酐、血小板覆盖率。
SELECT
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.ash_study.lactate_0_48h`) AS stays_with_lactate,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.ash_study.creatinine_0_48h`) AS stays_with_creatinine,
    (SELECT COUNT(DISTINCT stay_id) FROM `mimic-study-498508.ash_study.platelet_0_48h`) AS stays_with_platelet;

-- 目的：提取并清洗 0-48h SpO2 和 FiO2。
-- 原因：FiO2 常见 0.21-1.0 和 21-100 两种记录方式，必须统一为比例。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.spo2_0_48h` AS
SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime,
    DATETIME_DIFF(ce.charttime, c.icu_intime, MINUTE) / 60.0 AS hours_from_icu_intime,
    ce.itemid AS source_itemid,
    ce.valuenum AS spo2
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
    ON ce.stay_id = c.stay_id
WHERE ce.itemid = 220277
  AND ce.valuenum BETWEEN 50 AND 100
  AND ce.charttime >= c.icu_intime
  AND ce.charttime < DATETIME_ADD(c.icu_intime, INTERVAL 48 HOUR);

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.fio2_cleaned_0_48h` AS
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
INNER JOIN `mimic-study-498508.ash_study.eligible_icu_cohort` c
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
FROM `mimic-study-498508.ash_study.fio2_cleaned_0_48h`;

-- 目的：用 SpO2 前后 2 小时内最近 FiO2 计算 SpO2/FiO2。
-- 原因：SpO2 与 FiO2 不一定同一时间记录，最近邻匹配可提高氧合指标覆盖率。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.spo2_fio2_0_48h` AS
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
    FROM `mimic-study-498508.ash_study.spo2_0_48h` s
    INNER JOIN `mimic-study-498508.ash_study.fio2_cleaned_0_48h` f
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
FROM `mimic-study-498508.ash_study.spo2_fio2_0_48h`;

-- -----------------------------------------------------------------------------
-- 5. 0-48h 核心特征聚合宽表
-- -----------------------------------------------------------------------------

-- 目的：将明细指标聚合为一行一个 stay 的 0-48h 特征宽表。
-- 原因：K-means 聚类输入需要固定维度的样本特征矩阵。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.analysis_features_48h` AS
WITH hb AS (
    SELECT
        h.stay_id,
        MIN(h.hb) AS hb_min_48h_all,
        MIN(CASE
            WHEN rf.first_rbc_time_48h IS NULL OR h.charttime < rf.first_rbc_time_48h THEN h.hb
            ELSE NULL
        END) AS hb_min_48h_pre_transfusion,
        COUNT(*) AS hb_measurement_count
    FROM `mimic-study-498508.ash_study.hb_0_48h` h
    LEFT JOIN `mimic-study-498508.ash_study.rbc_transfusion_flags` rf
        ON h.stay_id = rf.stay_id
    GROUP BY h.stay_id
),
gcs AS (
    SELECT
        stay_id,
        MIN(gcs_motor) AS gcs_motor_min_48h,
        COUNT(*) AS gcs_motor_measurement_count
    FROM `mimic-study-498508.ash_study.gcs_motor_0_48h`
    GROUP BY stay_id
),
map_agg AS (
    SELECT
        stay_id,
        MIN(map_value) AS map_min_48h,
        AVG(map_value) AS map_mean_48h,
        COUNT(*) AS map_measurement_count
    FROM `mimic-study-498508.ash_study.map_0_48h`
    GROUP BY stay_id
),
si AS (
    SELECT
        stay_id,
        MAX(shock_index) AS shock_index_max_48h,
        AVG(shock_index) AS shock_index_mean_48h,
        COUNT(*) AS shock_index_measurement_count
    FROM `mimic-study-498508.ash_study.shock_index_0_48h`
    GROUP BY stay_id
),
lactate AS (
    SELECT
        stay_id,
        MAX(lactate) AS lactate_max_48h,
        AVG(lactate) AS lactate_mean_48h,
        COUNT(*) AS lactate_measurement_count
    FROM `mimic-study-498508.ash_study.lactate_0_48h`
    GROUP BY stay_id
),
oxygen AS (
    SELECT
        stay_id,
        MIN(spo2_fio2_ratio) AS spo2_fio2_min_48h,
        AVG(spo2_fio2_ratio) AS spo2_fio2_mean_48h,
        COUNT(*) AS spo2_fio2_measurement_count
    FROM `mimic-study-498508.ash_study.spo2_fio2_0_48h`
    GROUP BY stay_id
),
creatinine AS (
    SELECT
        stay_id,
        MAX(creatinine) AS creatinine_max_48h,
        AVG(creatinine) AS creatinine_mean_48h,
        COUNT(*) AS creatinine_measurement_count
    FROM `mimic-study-498508.ash_study.creatinine_0_48h`
    GROUP BY stay_id
),
platelet AS (
    SELECT
        stay_id,
        MIN(platelet) AS platelet_min_48h,
        AVG(platelet) AS platelet_mean_48h,
        COUNT(*) AS platelet_measurement_count
    FROM `mimic-study-498508.ash_study.platelet_0_48h`
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
    c.asah_evidence_level,
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
    gcs.gcs_motor_min_48h,
    map_agg.map_min_48h,
    map_agg.map_mean_48h,
    si.shock_index_max_48h,
    si.shock_index_mean_48h,
    lactate.lactate_max_48h,
    lactate.lactate_mean_48h,
    oxygen.spo2_fio2_min_48h,
    oxygen.spo2_fio2_mean_48h,
    creatinine.creatinine_max_48h,
    creatinine.creatinine_mean_48h,
    platelet.platelet_min_48h,
    platelet.platelet_mean_48h,
    CASE WHEN hb.hb_min_48h_all < 10 THEN 1 ELSE 0 END AS early_anemia_all,
    CASE WHEN hb.hb_min_48h_pre_transfusion < 10 THEN 1 ELSE 0 END AS early_anemia_pre_transfusion,
    CASE WHEN rf.first_rbc_time_48h IS NOT NULL AND hb.hb_min_48h_all IS NOT NULL THEN 1 ELSE 0 END AS has_hb_and_rbc_48h,
    (
        IF(hb.hb_min_48h_all IS NULL, 1, 0)
      + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
      + IF(map_agg.map_min_48h IS NULL, 1, 0)
      + IF(si.shock_index_max_48h IS NULL, 1, 0)
      + IF(lactate.lactate_max_48h IS NULL, 1, 0)
      + IF(oxygen.spo2_fio2_min_48h IS NULL, 1, 0)
      + IF(creatinine.creatinine_max_48h IS NULL, 1, 0)
      + IF(platelet.platelet_min_48h IS NULL, 1, 0)
    ) AS core_feature_missing_count,
    hb.hb_measurement_count,
    gcs.gcs_motor_measurement_count,
    map_agg.map_measurement_count,
    si.shock_index_measurement_count,
    lactate.lactate_measurement_count,
    oxygen.spo2_fio2_measurement_count,
    creatinine.creatinine_measurement_count,
    platelet.platelet_measurement_count
FROM `mimic-study-498508.ash_study.eligible_icu_cohort` c
LEFT JOIN `mimic-study-498508.ash_study.rbc_transfusion_flags` rf
    ON c.stay_id = rf.stay_id
LEFT JOIN hb
    ON c.stay_id = hb.stay_id
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
LEFT JOIN creatinine
    ON c.stay_id = creatinine.stay_id
LEFT JOIN platelet
    ON c.stay_id = platelet.stay_id;

-- 验证：检查核心变量覆盖率、缺失计数和主分析可纳入样本数。
SELECT
    COUNT(*) AS total_rows,
    COUNTIF(hb_min_48h_all IS NOT NULL) AS hb_nonmissing,
    COUNTIF(gcs_motor_min_48h IS NOT NULL) AS gcs_nonmissing,
    COUNTIF(map_min_48h IS NOT NULL) AS map_nonmissing,
    COUNTIF(shock_index_max_48h IS NOT NULL) AS shock_index_nonmissing,
    COUNTIF(lactate_max_48h IS NOT NULL) AS lactate_nonmissing,
    COUNTIF(spo2_fio2_min_48h IS NOT NULL) AS spo2_fio2_nonmissing,
    COUNTIF(creatinine_max_48h IS NOT NULL) AS creatinine_nonmissing,
    COUNTIF(platelet_min_48h IS NOT NULL) AS platelet_nonmissing,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0) AS eligible_primary_analysis_rows,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0 AND icu_los_hours >= 48) AS eligible_48h_los_sensitivity_rows,
    COUNTIF(core_feature_missing_count <= 2 AND massive_transfusion_24h = 0 AND any_rbc_transfusion_48h = 0) AS eligible_no_rbc_sensitivity_rows
FROM `mimic-study-498508.ash_study.analysis_features_48h`;

SELECT
    core_feature_missing_count,
    COUNT(*) AS rows_count
FROM `mimic-study-498508.ash_study.analysis_features_48h`
GROUP BY core_feature_missing_count
ORDER BY core_feature_missing_count;

-- 目的：生成主分析最终宽表。
-- 原因：Python 聚类和结局分析直接读取该表；仍保留敏感性分析所需标记。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.physiology_features_48h` AS
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
FROM `mimic-study-498508.ash_study.analysis_features_48h`;

-- 验证：最终宽表规模、主分析样本量、贫血比例和死亡率。
SELECT
    COUNT(*) AS all_feature_rows,
    COUNTIF(eligible_primary_analysis = 1) AS primary_analysis_rows,
    COUNTIF(eligible_sensitivity_48h_los = 1) AS sensitivity_48h_los_rows,
    COUNTIF(eligible_no_transfusion_sensitivity = 1) AS no_transfusion_sensitivity_rows,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(hospital_mortality AS FLOAT64) ELSE NULL END) AS primary_hospital_mortality_rate,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(early_anemia_all AS FLOAT64) ELSE NULL END) AS primary_early_anemia_rate,
    AVG(CASE WHEN eligible_primary_analysis = 1 THEN CAST(any_rbc_transfusion_48h AS FLOAT64) ELSE NULL END) AS primary_any_rbc_rate
FROM `mimic-study-498508.ash_study.physiology_features_48h`;

-- 验证：主分析样本中 8 个聚类变量范围。
SELECT
    MIN(hb_min_48h_all) AS min_hb_min_48h,
    MAX(hb_min_48h_all) AS max_hb_min_48h,
    MIN(gcs_motor_min_48h) AS min_gcs_motor_min_48h,
    MAX(gcs_motor_min_48h) AS max_gcs_motor_min_48h,
    MIN(map_min_48h) AS min_map_min_48h,
    MAX(map_min_48h) AS max_map_min_48h,
    MIN(shock_index_max_48h) AS min_shock_index_max_48h,
    MAX(shock_index_max_48h) AS max_shock_index_max_48h,
    MIN(lactate_max_48h) AS min_lactate_max_48h,
    MAX(lactate_max_48h) AS max_lactate_max_48h,
    MIN(spo2_fio2_min_48h) AS min_spo2_fio2_min_48h,
    MAX(spo2_fio2_min_48h) AS max_spo2_fio2_min_48h,
    MIN(creatinine_max_48h) AS min_creatinine_max_48h,
    MAX(creatinine_max_48h) AS max_creatinine_max_48h,
    MIN(platelet_min_48h) AS min_platelet_min_48h,
    MAX(platelet_min_48h) AS max_platelet_min_48h
FROM `mimic-study-498508.ash_study.physiology_features_48h`
WHERE eligible_primary_analysis = 1;

-- -----------------------------------------------------------------------------
-- 6. Flowchart 与建模前可行性检查
-- -----------------------------------------------------------------------------

-- 目的：生成 cohort flowchart 计数表。
-- 原因：论文需要逐步报告样本筛选过程，也方便发现样本损失最大的步骤。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.cohort_flowchart_counts` AS
SELECT '01_source_sah_admissions' AS step, COUNT(*) AS rows_count, COUNT(DISTINCT subject_id) AS patients, COUNT(DISTINCT hadm_id) AS admissions
FROM `mimic-study-498508.ash_study.source_sah_admissions`
UNION ALL
SELECT '02_adult_source_sah', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.ash_study.source_sah_admissions`
WHERE is_adult = 1
UNION ALL
SELECT '03_confirmed_asah_level_ge_2_no_trauma', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.ash_study.confirmed_asah_admissions`
UNION ALL
SELECT '04_first_icu_asah_stays', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.ash_study.first_icu_asah_stays`
UNION ALL
SELECT '05_icu_los_ge_24h', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.ash_study.eligible_icu_cohort`
UNION ALL
SELECT '06_core_missing_le_2', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.ash_study.physiology_features_48h`
WHERE core_feature_missing_count <= 2
UNION ALL
SELECT '07_primary_analysis_no_massive_transfusion', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.ash_study.physiology_features_48h`
WHERE eligible_primary_analysis = 1
UNION ALL
SELECT '08_sensitivity_icu_los_ge_48h', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.ash_study.physiology_features_48h`
WHERE eligible_sensitivity_48h_los = 1
UNION ALL
SELECT '09_sensitivity_no_rbc_48h', COUNT(*), COUNT(DISTINCT subject_id), COUNT(DISTINCT hadm_id)
FROM `mimic-study-498508.ash_study.physiology_features_48h`
WHERE eligible_no_transfusion_sensitivity = 1;

-- 验证：查看 flowchart 计数。
SELECT *
FROM `mimic-study-498508.ash_study.cohort_flowchart_counts`
ORDER BY step;

-- 目的：生成主分析样本的变量缺失率汇总。
-- 原因：Python 插补和建模前需要确认各变量缺失程度。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.feature_missingness_summary` AS
SELECT 'hb_min_48h_all' AS feature, COUNTIF(hb_min_48h_all IS NULL) AS missing_n, COUNT(*) AS total_n, COUNTIF(hb_min_48h_all IS NULL) / COUNT(*) AS missing_rate
FROM `mimic-study-498508.ash_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'gcs_motor_min_48h', COUNTIF(gcs_motor_min_48h IS NULL), COUNT(*), COUNTIF(gcs_motor_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.ash_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'map_min_48h', COUNTIF(map_min_48h IS NULL), COUNT(*), COUNTIF(map_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.ash_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'shock_index_max_48h', COUNTIF(shock_index_max_48h IS NULL), COUNT(*), COUNTIF(shock_index_max_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.ash_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'lactate_max_48h', COUNTIF(lactate_max_48h IS NULL), COUNT(*), COUNTIF(lactate_max_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.ash_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'spo2_fio2_min_48h', COUNTIF(spo2_fio2_min_48h IS NULL), COUNT(*), COUNTIF(spo2_fio2_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.ash_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'creatinine_max_48h', COUNTIF(creatinine_max_48h IS NULL), COUNT(*), COUNTIF(creatinine_max_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.ash_study.physiology_features_48h` WHERE eligible_primary_analysis = 1
UNION ALL
SELECT 'platelet_min_48h', COUNTIF(platelet_min_48h IS NULL), COUNT(*), COUNTIF(platelet_min_48h IS NULL) / COUNT(*)
FROM `mimic-study-498508.ash_study.physiology_features_48h` WHERE eligible_primary_analysis = 1;

-- 验证：查看缺失率汇总。
SELECT *
FROM `mimic-study-498508.ash_study.feature_missingness_summary`
ORDER BY missing_rate DESC;

-- 目的：输出建模前 feasibility 基线表框架。
-- 原因：聚类完成后应按 phenotype 补充 N、死亡、贫血、贫血死亡等计数，判断分层回归是否稳定。
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.pre_clustering_feasibility_summary` AS
SELECT
    eligible_primary_analysis,
    COUNT(*) AS n,
    COUNTIF(hospital_mortality = 1) AS deaths,
    COUNTIF(early_anemia_all = 1) AS anemia_n,
    COUNTIF(early_anemia_all = 0) AS non_anemia_n,
    COUNTIF(early_anemia_all = 1 AND hospital_mortality = 1) AS anemia_deaths,
    COUNTIF(early_anemia_all = 0 AND hospital_mortality = 1) AS non_anemia_deaths
FROM `mimic-study-498508.ash_study.physiology_features_48h`
GROUP BY eligible_primary_analysis;

-- 验证：查看聚类前总体可行性计数。
SELECT *
FROM `mimic-study-498508.ash_study.pre_clustering_feasibility_summary`
ORDER BY eligible_primary_analysis DESC;

