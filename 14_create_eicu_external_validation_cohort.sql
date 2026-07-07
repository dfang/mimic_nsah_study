-- eICU external validation cohort and 0-48h physiology feature extraction
-- Data source: physionet-data.eicu_crd
-- Target dataset: mimic-study-498508.eicu_sah_validation
--
-- Design:
-- 1. Build an adult first-ICU non-traumatic SAH cohort from eICU diagnosis text/ICD evidence.
-- 2. Extract the same 0-48h core domains used in the MIMIC primary phenotype model:
--    Hb, GCS motor, MAP, shock index, SpO2, creatinine, INR, and platelet.
-- 3. Do not exclude massive transfusion in the primary eICU cohort because eICU transfusion
--    units are heterogeneous; recorded RBC exposure is retained for sensitivity analysis.

CREATE SCHEMA IF NOT EXISTS `mimic-study-498508.eicu_sah_validation`
OPTIONS(location = 'US');

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_source_schema_audit` AS
SELECT
    table_name,
    STRING_AGG(column_name, ', ' ORDER BY ordinal_position) AS available_columns
FROM `physionet-data.eicu_crd.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN (
    'patient',
    'diagnosis',
    'lab',
    'nursecharting',
    'apacheapsvar',
    'apachepatientresult',
    'vitalperiodic',
    'vitalaperiodic',
    'infusiondrug',
    'intakeoutput'
)
GROUP BY table_name;

-- SAH evidence uses eICU diagnosis text and ICD-9 code 430 where available.
-- Trauma exclusions are deliberately broad and audited through text examples.
CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_sah_diagnosis_evidence` AS
WITH diagnosis_evidence AS (
    SELECT
        d.patientunitstayid,
        MAX(CASE WHEN REGEXP_CONTAINS(LOWER(COALESCE(d.icd9code, '')), r'(^|,| )430($|,| )') THEN 1 ELSE 0 END) AS sah_from_icd,
        MAX(CASE WHEN REGEXP_CONTAINS(LOWER(COALESCE(d.diagnosisstring, '')), r'subarachnoid') THEN 1 ELSE 0 END) AS sah_from_text,
        MAX(
            CASE
                WHEN REGEXP_CONTAINS(LOWER(COALESCE(d.diagnosisstring, '')), r'traumatic|trauma|head injury|skull fracture') THEN 1
                ELSE 0
            END
        ) AS traumatic_sah_flag,
        STRING_AGG(DISTINCT COALESCE(d.icd9code, ''), ', ' ORDER BY COALESCE(d.icd9code, '')) AS diagnosis_codes,
        STRING_AGG(DISTINCT SUBSTR(COALESCE(d.diagnosisstring, ''), 1, 180), ' | ' LIMIT 5) AS diagnosis_text_examples
    FROM `physionet-data.eicu_crd.diagnosis` d
    GROUP BY d.patientunitstayid
),
admission_dx_evidence AS (
    SELECT
        p.patientunitstayid,
        CASE WHEN REGEXP_CONTAINS(LOWER(COALESCE(p.apacheadmissiondx, '')), r'subarachnoid') THEN 1 ELSE 0 END AS sah_from_admission_text,
        CASE
            WHEN REGEXP_CONTAINS(LOWER(COALESCE(p.apacheadmissiondx, '')), r'traumatic|trauma|head injury|skull fracture') THEN 1
            ELSE 0
        END AS traumatic_admission_flag,
        SUBSTR(COALESCE(p.apacheadmissiondx, ''), 1, 180) AS admission_dx_example
    FROM `physionet-data.eicu_crd.patient` p
)
SELECT
    p.patientunitstayid,
    GREATEST(COALESCE(de.sah_from_icd, 0), 0) AS sah_from_icd,
    COALESCE(de.sah_from_text, 0) AS sah_from_diagnosis_text,
    COALESCE(adx.sah_from_admission_text, 0) AS sah_from_admission_text,
    GREATEST(COALESCE(de.sah_from_text, 0), COALESCE(adx.sah_from_admission_text, 0)) AS sah_from_text,
    GREATEST(COALESCE(de.traumatic_sah_flag, 0), COALESCE(adx.traumatic_admission_flag, 0)) AS traumatic_sah_flag,
    CONCAT(
        CASE WHEN COALESCE(de.sah_from_icd, 0) = 1 THEN 'diagnosis_icd9_430;' ELSE '' END,
        CASE WHEN COALESCE(de.sah_from_text, 0) = 1 THEN 'diagnosis_text;' ELSE '' END,
        CASE WHEN COALESCE(adx.sah_from_admission_text, 0) = 1 THEN 'apache_admissiondx_text;' ELSE '' END
    ) AS diagnosis_sources,
    de.diagnosis_codes,
    CONCAT(COALESCE(de.diagnosis_text_examples, ''), ' | admissionDx: ', COALESCE(adx.admission_dx_example, '')) AS diagnosis_text_examples
FROM `physionet-data.eicu_crd.patient` p
LEFT JOIN diagnosis_evidence de
    ON p.patientunitstayid = de.patientunitstayid
LEFT JOIN admission_dx_evidence adx
    ON p.patientunitstayid = adx.patientunitstayid
WHERE GREATEST(COALESCE(de.sah_from_icd, 0), COALESCE(de.sah_from_text, 0), COALESCE(adx.sah_from_admission_text, 0)) = 1;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` AS
WITH base AS (
    SELECT
        p.patientunitstayid,
        p.patienthealthsystemstayid,
        p.uniquepid,
        p.hospitalid,
        p.wardid,
        p.gender,
        p.age AS age_raw,
        CASE
            WHEN p.age = '> 89' THEN 90
            ELSE SAFE_CAST(p.age AS INT64)
        END AS age,
        p.ethnicity AS race,
        p.apacheadmissiondx,
        p.hospitaladmitsource,
        p.unitadmitsource,
        p.unittype,
        p.unitstaytype,
        p.admissionweight,
        p.hospitaladmitoffset,
        p.hospitaldischargeoffset,
        p.unitdischargeoffset,
        p.hospitaldischargestatus,
        p.unitdischargestatus,
        p.unitdischargelocation,
        p.unitvisitnumber,
        dx.sah_from_icd,
        dx.sah_from_diagnosis_text,
        dx.sah_from_admission_text,
        dx.sah_from_text,
        dx.traumatic_sah_flag,
        dx.diagnosis_sources,
        dx.diagnosis_codes,
        dx.diagnosis_text_examples,
        ROW_NUMBER() OVER (
            PARTITION BY p.uniquepid
            ORDER BY p.unitvisitnumber, p.patientunitstayid
        ) AS icu_stay_rank
    FROM `physionet-data.eicu_crd.patient` p
    INNER JOIN `mimic-study-498508.eicu_sah_validation.eicu_sah_diagnosis_evidence` dx
        ON p.patientunitstayid = dx.patientunitstayid
)
SELECT
    *,
    CASE WHEN age >= 18 THEN 1 ELSE 0 END AS is_adult,
    CASE WHEN icu_stay_rank = 1 THEN 1 ELSE 0 END AS is_first_icu_stay,
    unitdischargeoffset AS icu_los_minutes,
    unitdischargeoffset / 60.0 AS icu_los_hours,
    unitdischargeoffset / 1440.0 AS icu_los_days,
    (hospitaldischargeoffset - hospitaladmitoffset) / 1440.0 AS hospital_los_days,
    CASE WHEN unitdischargeoffset >= 24 * 60 THEN 1 ELSE 0 END AS icu_los_ge_24h,
    CASE WHEN unitdischargeoffset >= 48 * 60 THEN 1 ELSE 0 END AS icu_los_ge_48h,
    CASE WHEN LOWER(COALESCE(hospitaldischargestatus, '')) = 'expired' THEN 1 ELSE 0 END AS hospital_mortality,
    CASE WHEN LOWER(COALESCE(unitdischargestatus, '')) = 'expired' THEN 1 ELSE 0 END AS icu_mortality,
    CASE
        WHEN sah_from_icd = 1 THEN 2
        WHEN sah_from_diagnosis_text = 1 THEN 2
        WHEN sah_from_admission_text = 1 THEN 1
        ELSE 0
    END AS nsah_evidence_level,
    CASE WHEN traumatic_sah_flag = 0 AND (sah_from_icd = 1 OR sah_from_diagnosis_text = 1) THEN 1 ELSE 0 END AS strict_sah_evidence,
    CASE
        WHEN age >= 18
         AND icu_stay_rank = 1
         AND traumatic_sah_flag = 0
         AND unitdischargeoffset >= 24 * 60 THEN 1
        ELSE 0
    END AS eligible_base_cohort
FROM base;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_lab_features_48h` AS
SELECT
    c.patientunitstayid,
    MIN(CASE WHEN LOWER(l.labname) IN ('hgb', 'hemoglobin') AND l.labresult BETWEEN 3 AND 25 THEN l.labresult END) AS hb_min_48h_all,
    MAX(CASE WHEN LOWER(l.labname) = 'creatinine' AND l.labresult BETWEEN 0.1 AND 20 THEN l.labresult END) AS creatinine_max_48h,
    MAX(CASE WHEN LOWER(l.labname) = 'pt - inr' AND l.labresult BETWEEN 0.5 AND 20 THEN l.labresult END) AS inr_max_48h,
    MIN(CASE WHEN LOWER(l.labname) IN ('platelets', 'platelet x 1000', 'platelets x 1000') AND l.labresult BETWEEN 5 AND 1500 THEN l.labresult END) AS platelet_min_48h,
    MAX(CASE WHEN LOWER(l.labname) = 'lactate' AND l.labresult BETWEEN 0.1 AND 30 THEN l.labresult END) AS lactate_max_48h,
    COUNTIF(LOWER(l.labname) IN ('hgb', 'hemoglobin') AND l.labresult BETWEEN 3 AND 25) AS hb_measurement_count_48h,
    COUNTIF(LOWER(l.labname) = 'creatinine' AND l.labresult BETWEEN 0.1 AND 20) AS creatinine_measurement_count_48h,
    COUNTIF(LOWER(l.labname) = 'pt - inr' AND l.labresult BETWEEN 0.5 AND 20) AS inr_measurement_count_48h,
    COUNTIF(LOWER(l.labname) IN ('platelets', 'platelet x 1000', 'platelets x 1000') AND l.labresult BETWEEN 5 AND 1500) AS platelet_measurement_count_48h
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
LEFT JOIN `physionet-data.eicu_crd.lab` l
    ON c.patientunitstayid = l.patientunitstayid
   AND l.labresultoffset >= 0
   AND l.labresultoffset < 48 * 60
WHERE c.eligible_base_cohort = 1
GROUP BY c.patientunitstayid;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_gcs_features` AS
WITH charted AS (
    SELECT
        c.patientunitstayid,
        nc.nursingchartoffset,
        LOWER(COALESCE(nc.nursingchartcelltypevallabel, '')) AS label,
        LOWER(COALESCE(nc.nursingchartcelltypevalname, '')) AS name,
        LOWER(COALESCE(nc.nursingchartvalue, '')) AS value_text,
        SAFE_CAST(nc.nursingchartvalue AS FLOAT64) AS value_num
    FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
    INNER JOIN `physionet-data.eicu_crd.nursecharting` nc
        ON c.patientunitstayid = nc.patientunitstayid
    WHERE c.eligible_base_cohort = 1
      AND nc.nursingchartoffset >= 0
      AND nc.nursingchartoffset < 48 * 60
      AND (
          LOWER(COALESCE(nc.nursingchartcelltypevallabel, '')) LIKE '%glasgow coma score%'
       OR LOWER(COALESCE(nc.nursingchartcelltypevalname, '')) LIKE '%gcs%'
       OR LOWER(COALESCE(nc.nursingchartcelltypevalname, '')) = 'motor'
       OR LOWER(COALESCE(nc.nursingchartcelltypevallabel, '')) LIKE '%motor response%'
      )
),
scored AS (
    SELECT
        patientunitstayid,
        CASE
            WHEN name = 'gcs total' AND value_num BETWEEN 3 AND 15 THEN value_num
            ELSE NULL
        END AS gcs_total,
        CASE
            WHEN name = 'motor' AND value_num BETWEEN 1 AND 6 THEN value_num
            WHEN label LIKE '%motor%' AND value_num BETWEEN 1 AND 6 THEN value_num
            WHEN value_text LIKE '%obeys%' THEN 6
            WHEN value_text LIKE '%localiz%' THEN 5
            WHEN value_text LIKE '%withdraw%' THEN 4
            WHEN value_text LIKE '%flex%' OR value_text LIKE '%decortic%' THEN 3
            WHEN value_text LIKE '%extend%' OR value_text LIKE '%decerebr%' THEN 2
            WHEN value_text LIKE '%none%' OR value_text LIKE '%no response%' THEN 1
            ELSE NULL
        END AS gcs_motor
    FROM charted
),
apache_fallback AS (
    SELECT
        patientunitstayid,
        MIN(CASE WHEN motor BETWEEN 1 AND 6 THEN motor END) AS apache_motor_min
    FROM `physionet-data.eicu_crd.apacheapsvar`
    GROUP BY patientunitstayid
)
SELECT
    c.patientunitstayid,
    MIN(s.gcs_total) AS gcs_min_48h,
    COALESCE(MIN(s.gcs_motor), MIN(af.apache_motor_min)) AS gcs_motor_min_48h,
    CASE
        WHEN MIN(s.gcs_total) IS NULL THEN NULL
        WHEN MIN(s.gcs_total) <= 6 THEN 4
        WHEN MIN(s.gcs_total) <= 9 THEN 3
        WHEN MIN(s.gcs_total) <= 12 THEN 2
        ELSE 1
    END AS gcs_grade_min_48h,
    COUNTIF(s.gcs_total IS NOT NULL) AS gcs_total_measurement_count_48h,
    COUNTIF(s.gcs_motor IS NOT NULL) AS gcs_motor_measurement_count_48h
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
LEFT JOIN scored s
    ON c.patientunitstayid = s.patientunitstayid
LEFT JOIN apache_fallback af
    ON c.patientunitstayid = af.patientunitstayid
WHERE c.eligible_base_cohort = 1
GROUP BY c.patientunitstayid;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_vital_features_48h` AS
WITH periodic AS (
    SELECT
        c.patientunitstayid,
        vp.observationoffset,
        CASE WHEN vp.systemicmean BETWEEN 20 AND 200 THEN vp.systemicmean END AS map_value,
        CASE WHEN vp.systemicsystolic BETWEEN 40 AND 300 THEN vp.systemicsystolic END AS sbp_value,
        CASE WHEN vp.heartrate BETWEEN 20 AND 250 THEN vp.heartrate END AS hr_value,
        CASE WHEN vp.sao2 BETWEEN 40 AND 100 THEN vp.sao2 END AS spo2_value
    FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
    INNER JOIN `physionet-data.eicu_crd.vitalperiodic` vp
        ON c.patientunitstayid = vp.patientunitstayid
    WHERE c.eligible_base_cohort = 1
      AND vp.observationoffset >= 0
      AND vp.observationoffset < 48 * 60
),
periodic_agg AS (
    SELECT
        patientunitstayid,
        MIN(map_value) AS periodic_map_min_48h,
        MIN(sbp_value) AS periodic_sbp_min_48h,
        MIN(spo2_value) AS spo2_min_48h,
        COUNTIF(map_value IS NOT NULL) AS periodic_map_measurement_count_48h,
        COUNTIF(sbp_value IS NOT NULL) AS periodic_sbp_measurement_count_48h,
        COUNTIF(hr_value IS NOT NULL) AS hr_measurement_count_48h,
        COUNTIF(spo2_value IS NOT NULL) AS spo2_measurement_count_48h
    FROM periodic
    GROUP BY patientunitstayid
),
hr_events AS (
    SELECT
        patientunitstayid,
        observationoffset AS hr_offset,
        hr_value
    FROM periodic
    WHERE hr_value IS NOT NULL
),
aperiodic AS (
    SELECT
        c.patientunitstayid,
        va.observationoffset,
        CASE WHEN va.noninvasivemean BETWEEN 20 AND 200 THEN va.noninvasivemean END AS map_value,
        CASE WHEN va.noninvasivesystolic BETWEEN 40 AND 300 THEN va.noninvasivesystolic END AS sbp_value
    FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
    INNER JOIN `physionet-data.eicu_crd.vitalaperiodic` va
        ON c.patientunitstayid = va.patientunitstayid
    WHERE c.eligible_base_cohort = 1
      AND va.observationoffset >= 0
      AND va.observationoffset < 48 * 60
),
aperiodic_agg AS (
    SELECT
        patientunitstayid,
        MIN(map_value) AS aperiodic_map_min_48h,
        MIN(sbp_value) AS aperiodic_sbp_min_48h,
        COUNTIF(map_value IS NOT NULL) AS aperiodic_map_measurement_count_48h,
        COUNTIF(sbp_value IS NOT NULL) AS aperiodic_sbp_measurement_count_48h
    FROM aperiodic
    GROUP BY patientunitstayid
),
sbp_events AS (
    SELECT
        patientunitstayid,
        observationoffset AS sbp_offset,
        sbp_value,
        'periodic' AS sbp_source
    FROM periodic
    WHERE sbp_value IS NOT NULL
    UNION ALL
    SELECT
        patientunitstayid,
        observationoffset AS sbp_offset,
        sbp_value,
        'aperiodic' AS sbp_source
    FROM aperiodic
    WHERE sbp_value IS NOT NULL
),
nearest_sbp_pairs AS (
    SELECT
        h.patientunitstayid,
        h.hr_offset,
        h.hr_value,
        s.sbp_offset,
        s.sbp_value,
        s.sbp_source,
        ABS(h.hr_offset - s.sbp_offset) AS pairing_gap_min
    FROM hr_events h
    INNER JOIN sbp_events s
        ON h.patientunitstayid = s.patientunitstayid
       AND ABS(h.hr_offset - s.sbp_offset) <= 15
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY h.patientunitstayid, h.hr_offset
        ORDER BY ABS(h.hr_offset - s.sbp_offset), s.sbp_offset
    ) = 1
),
shock_index_agg AS (
    SELECT
        patientunitstayid,
        MAX(hr_value / sbp_value) AS shock_index_max_48h,
        COUNT(*) AS shock_index_pair_count_48h,
        APPROX_QUANTILES(pairing_gap_min, 100)[OFFSET(50)] AS shock_index_median_pairing_gap_min,
        COUNTIF(sbp_source = 'aperiodic') AS shock_index_aperiodic_sbp_pair_count_48h
    FROM nearest_sbp_pairs
    GROUP BY patientunitstayid
)
SELECT
    c.patientunitstayid,
    NULLIF(LEAST(
        COALESCE(pa.periodic_map_min_48h, 9999),
        COALESCE(aa.aperiodic_map_min_48h, 9999)
    ), 9999) AS map_min_48h,
    NULLIF(LEAST(
        COALESCE(pa.periodic_sbp_min_48h, 9999),
        COALESCE(aa.aperiodic_sbp_min_48h, 9999)
    ), 9999) AS sbp_min_48h,
    si.shock_index_max_48h,
    pa.spo2_min_48h,
    COALESCE(pa.periodic_map_measurement_count_48h, 0) + COALESCE(aa.aperiodic_map_measurement_count_48h, 0) AS map_measurement_count_48h,
    COALESCE(pa.periodic_sbp_measurement_count_48h, 0) + COALESCE(aa.aperiodic_sbp_measurement_count_48h, 0) AS sbp_measurement_count_48h,
    COALESCE(pa.hr_measurement_count_48h, 0) AS hr_measurement_count_48h,
    COALESCE(pa.spo2_measurement_count_48h, 0) AS spo2_measurement_count_48h,
    COALESCE(si.shock_index_pair_count_48h, 0) AS shock_index_pair_count_48h,
    si.shock_index_median_pairing_gap_min,
    COALESCE(si.shock_index_aperiodic_sbp_pair_count_48h, 0) AS shock_index_aperiodic_sbp_pair_count_48h
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
LEFT JOIN periodic_agg pa
    ON c.patientunitstayid = pa.patientunitstayid
LEFT JOIN aperiodic_agg aa
    ON c.patientunitstayid = aa.patientunitstayid
LEFT JOIN shock_index_agg si
    ON c.patientunitstayid = si.patientunitstayid
WHERE c.eligible_base_cohort = 1
;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_rbc_exposure_48h` AS
WITH infusion AS (
    SELECT
        c.patientunitstayid,
        COUNT(*) AS events,
        SUM(SAFE_CAST(id.drugamount AS FLOAT64)) AS amount,
        STRING_AGG(DISTINCT CAST(id.drugname AS STRING), ', ' LIMIT 5) AS examples
    FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
    INNER JOIN `physionet-data.eicu_crd.infusiondrug` id
        ON c.patientunitstayid = id.patientunitstayid
    WHERE c.eligible_base_cohort = 1
      AND id.infusionoffset >= 0
      AND id.infusionoffset < 48 * 60
      AND REGEXP_CONTAINS(LOWER(COALESCE(id.drugname, '')), r'\\brbc\\b|red blood|packed red|prbc')
    GROUP BY c.patientunitstayid
),
intake AS (
    SELECT
        c.patientunitstayid,
        COUNT(*) AS events,
        SUM(io.cellvaluenumeric) AS amount,
        STRING_AGG(
            DISTINCT CONCAT(COALESCE(CAST(io.celllabel AS STRING), ''), ':', COALESCE(CAST(io.cellvaluetext AS STRING), '')),
            ', ' LIMIT 5
        ) AS examples
    FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
    INNER JOIN `physionet-data.eicu_crd.intakeoutput` io
        ON c.patientunitstayid = io.patientunitstayid
    WHERE c.eligible_base_cohort = 1
      AND io.intakeoutputoffset >= 0
      AND io.intakeoutputoffset < 48 * 60
      AND REGEXP_CONTAINS(
          LOWER(CONCAT(
              COALESCE(CAST(io.cellpath AS STRING), ''),
              ' ',
              COALESCE(CAST(io.celllabel AS STRING), ''),
              ' ',
              COALESCE(CAST(io.cellvaluetext AS STRING), '')
          )),
          r'\\brbc\\b|red blood|packed red|prbc'
      )
    GROUP BY c.patientunitstayid
)
SELECT
    c.patientunitstayid,
    CASE WHEN COALESCE(i.events, 0) + COALESCE(o.events, 0) > 0 THEN 1 ELSE 0 END AS any_rbc_transfusion_48h,
    COALESCE(i.events, 0) + COALESCE(o.events, 0) AS rbc_events_48h,
    COALESCE(i.amount, 0) + COALESCE(o.amount, 0) AS rbc_recorded_amount_48h,
    CONCAT(
        CASE WHEN COALESCE(i.events, 0) > 0 THEN 'infusiondrug;' ELSE '' END,
        CASE WHEN COALESCE(o.events, 0) > 0 THEN 'intakeoutput;' ELSE '' END
    ) AS rbc_source_tables,
    CONCAT(COALESCE(i.examples, ''), ' | ', COALESCE(o.examples, '')) AS rbc_text_examples
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
LEFT JOIN infusion i
    ON c.patientunitstayid = i.patientunitstayid
LEFT JOIN intake o
    ON c.patientunitstayid = o.patientunitstayid
WHERE c.eligible_base_cohort = 1;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_apache_severity` AS
SELECT
    patientunitstayid,
    MAX(SAFE_CAST(acutephysiologyscore AS FLOAT64)) AS acutephysiologyscore,
    MAX(SAFE_CAST(apachescore AS FLOAT64)) AS apachescore,
    MAX(SAFE_CAST(predictedicumortality AS FLOAT64)) AS predictedicumortality,
    MAX(SAFE_CAST(predictedhospitalmortality AS FLOAT64)) AS predictedhospitalmortality,
    MAX(SAFE_CAST(predictediculos AS FLOAT64)) AS predictediculos,
    MAX(SAFE_CAST(predictedhospitallos AS FLOAT64)) AS predictedhospitallos
FROM `physionet-data.eicu_crd.apachepatientresult`
GROUP BY patientunitstayid;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h` AS
SELECT
    c.patientunitstayid,
    c.patienthealthsystemstayid,
    c.uniquepid,
    c.hospitalid,
    c.wardid,
    c.gender,
    c.age,
    c.age_raw,
    c.race,
    c.apacheadmissiondx AS admission_type,
    c.hospitaladmitsource,
    c.unitadmitsource,
    c.unittype,
    c.unitstaytype,
    c.nsah_evidence_level,
    c.strict_sah_evidence,
    c.sah_from_icd,
    c.sah_from_diagnosis_text,
    c.sah_from_admission_text,
    c.sah_from_text,
    c.traumatic_sah_flag,
    c.diagnosis_sources,
    c.diagnosis_codes,
    c.diagnosis_text_examples,
    c.icu_los_hours,
    c.icu_los_days,
    c.hospital_los_days,
    c.icu_los_ge_48h,
    c.hospital_mortality,
    c.icu_mortality,
    lab.hb_min_48h_all,
    CASE WHEN lab.hb_min_48h_all < 10 THEN 1 WHEN lab.hb_min_48h_all IS NULL THEN NULL ELSE 0 END AS early_anemia_all,
    gcs.gcs_min_48h,
    gcs.gcs_grade_min_48h,
    gcs.gcs_motor_min_48h,
    vit.map_min_48h,
    vit.sbp_min_48h,
    vit.shock_index_max_48h,
    vit.spo2_min_48h,
    vit.shock_index_pair_count_48h,
    vit.shock_index_median_pairing_gap_min,
    vit.shock_index_aperiodic_sbp_pair_count_48h,
    lab.creatinine_max_48h,
    lab.inr_max_48h,
    lab.platelet_min_48h,
    lab.lactate_max_48h,
    lab.hb_measurement_count_48h,
    lab.creatinine_measurement_count_48h,
    lab.inr_measurement_count_48h,
    lab.platelet_measurement_count_48h,
    vit.map_measurement_count_48h,
    vit.sbp_measurement_count_48h,
    vit.hr_measurement_count_48h,
    vit.spo2_measurement_count_48h,
    rbc.any_rbc_transfusion_48h,
    rbc.rbc_events_48h,
    rbc.rbc_recorded_amount_48h,
    rbc.rbc_source_tables,
    rbc.rbc_text_examples,
    ap.acutephysiologyscore,
    ap.apachescore,
    ap.predictedicumortality,
    ap.predictedhospitalmortality,
    ap.predictediculos,
    ap.predictedhospitallos,
    (
        IF(lab.hb_min_48h_all IS NULL, 1, 0)
      + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
      + IF(vit.map_min_48h IS NULL, 1, 0)
      + IF(vit.shock_index_max_48h IS NULL, 1, 0)
      + IF(vit.spo2_min_48h IS NULL, 1, 0)
      + IF(lab.creatinine_max_48h IS NULL, 1, 0)
      + IF(lab.inr_max_48h IS NULL, 1, 0)
      + IF(lab.platelet_min_48h IS NULL, 1, 0)
    ) AS core_feature_missing_count,
    CASE
        WHEN (
            IF(lab.hb_min_48h_all IS NULL, 1, 0)
          + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
          + IF(vit.map_min_48h IS NULL, 1, 0)
          + IF(vit.shock_index_max_48h IS NULL, 1, 0)
          + IF(vit.spo2_min_48h IS NULL, 1, 0)
          + IF(lab.creatinine_max_48h IS NULL, 1, 0)
          + IF(lab.inr_max_48h IS NULL, 1, 0)
          + IF(lab.platelet_min_48h IS NULL, 1, 0)
        ) <= 2 THEN 1
        ELSE 0
    END AS eligible_external_validation,
    CASE
        WHEN c.icu_los_ge_48h = 1
         AND (
            IF(lab.hb_min_48h_all IS NULL, 1, 0)
          + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
          + IF(vit.map_min_48h IS NULL, 1, 0)
          + IF(vit.shock_index_max_48h IS NULL, 1, 0)
          + IF(vit.spo2_min_48h IS NULL, 1, 0)
          + IF(lab.creatinine_max_48h IS NULL, 1, 0)
          + IF(lab.inr_max_48h IS NULL, 1, 0)
          + IF(lab.platelet_min_48h IS NULL, 1, 0)
        ) <= 2 THEN 1
        ELSE 0
    END AS eligible_external_los48_sensitivity,
    CASE
        WHEN COALESCE(rbc.any_rbc_transfusion_48h, 0) = 0
         AND (
            IF(lab.hb_min_48h_all IS NULL, 1, 0)
          + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
          + IF(vit.map_min_48h IS NULL, 1, 0)
          + IF(vit.shock_index_max_48h IS NULL, 1, 0)
          + IF(vit.spo2_min_48h IS NULL, 1, 0)
          + IF(lab.creatinine_max_48h IS NULL, 1, 0)
          + IF(lab.inr_max_48h IS NULL, 1, 0)
          + IF(lab.platelet_min_48h IS NULL, 1, 0)
        ) <= 2 THEN 1
        ELSE 0
    END AS eligible_external_no_rbc_sensitivity,
    CASE
        WHEN c.strict_sah_evidence = 1
         AND (
            IF(lab.hb_min_48h_all IS NULL, 1, 0)
          + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
          + IF(vit.map_min_48h IS NULL, 1, 0)
          + IF(vit.shock_index_max_48h IS NULL, 1, 0)
          + IF(vit.spo2_min_48h IS NULL, 1, 0)
          + IF(lab.creatinine_max_48h IS NULL, 1, 0)
          + IF(lab.inr_max_48h IS NULL, 1, 0)
          + IF(lab.platelet_min_48h IS NULL, 1, 0)
        ) <= 2 THEN 1
        ELSE 0
    END AS eligible_external_strict_sah_sensitivity,
    CASE
        WHEN (
            IF(lab.hb_min_48h_all IS NULL, 1, 0)
          + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
          + IF(vit.map_min_48h IS NULL, 1, 0)
          + IF(vit.shock_index_max_48h IS NULL, 1, 0)
          + IF(vit.spo2_min_48h IS NULL, 1, 0)
          + IF(lab.creatinine_max_48h IS NULL, 1, 0)
          + IF(lab.inr_max_48h IS NULL, 1, 0)
          + IF(lab.platelet_min_48h IS NULL, 1, 0)
        ) <= 1 THEN 1
        ELSE 0
    END AS eligible_external_low_missing_sensitivity,
    CASE
        WHEN (
            IF(lab.hb_min_48h_all IS NULL, 1, 0)
          + IF(gcs.gcs_motor_min_48h IS NULL, 1, 0)
          + IF(vit.map_min_48h IS NULL, 1, 0)
          + IF(vit.shock_index_max_48h IS NULL, 1, 0)
          + IF(vit.spo2_min_48h IS NULL, 1, 0)
          + IF(lab.creatinine_max_48h IS NULL, 1, 0)
          + IF(lab.inr_max_48h IS NULL, 1, 0)
          + IF(lab.platelet_min_48h IS NULL, 1, 0)
        ) = 0 THEN 1
        ELSE 0
    END AS eligible_external_complete_case_sensitivity
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort` c
LEFT JOIN `mimic-study-498508.eicu_sah_validation.eicu_lab_features_48h` lab
    ON c.patientunitstayid = lab.patientunitstayid
LEFT JOIN `mimic-study-498508.eicu_sah_validation.eicu_gcs_features` gcs
    ON c.patientunitstayid = gcs.patientunitstayid
LEFT JOIN `mimic-study-498508.eicu_sah_validation.eicu_vital_features_48h` vit
    ON c.patientunitstayid = vit.patientunitstayid
LEFT JOIN `mimic-study-498508.eicu_sah_validation.eicu_rbc_exposure_48h` rbc
    ON c.patientunitstayid = rbc.patientunitstayid
LEFT JOIN `mimic-study-498508.eicu_sah_validation.eicu_apache_severity` ap
    ON c.patientunitstayid = ap.patientunitstayid
WHERE c.eligible_base_cohort = 1;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_feature_missingness_summary` AS
SELECT 'hb_min_48h_all' AS feature, COUNT(*) AS total_n, COUNTIF(hb_min_48h_all IS NULL) AS missing_n, COUNTIF(hb_min_48h_all IS NULL) / COUNT(*) AS missing_rate, COUNTIF(hb_min_48h_all IS NOT NULL) AS nonmissing_n
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
UNION ALL SELECT 'gcs_motor_min_48h', COUNT(*), COUNTIF(gcs_motor_min_48h IS NULL), COUNTIF(gcs_motor_min_48h IS NULL) / COUNT(*), COUNTIF(gcs_motor_min_48h IS NOT NULL)
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
UNION ALL SELECT 'map_min_48h', COUNT(*), COUNTIF(map_min_48h IS NULL), COUNTIF(map_min_48h IS NULL) / COUNT(*), COUNTIF(map_min_48h IS NOT NULL)
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
UNION ALL SELECT 'shock_index_max_48h', COUNT(*), COUNTIF(shock_index_max_48h IS NULL), COUNTIF(shock_index_max_48h IS NULL) / COUNT(*), COUNTIF(shock_index_max_48h IS NOT NULL)
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
UNION ALL SELECT 'spo2_min_48h', COUNT(*), COUNTIF(spo2_min_48h IS NULL), COUNTIF(spo2_min_48h IS NULL) / COUNT(*), COUNTIF(spo2_min_48h IS NOT NULL)
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
UNION ALL SELECT 'creatinine_max_48h', COUNT(*), COUNTIF(creatinine_max_48h IS NULL), COUNTIF(creatinine_max_48h IS NULL) / COUNT(*), COUNTIF(creatinine_max_48h IS NOT NULL)
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
UNION ALL SELECT 'inr_max_48h', COUNT(*), COUNTIF(inr_max_48h IS NULL), COUNTIF(inr_max_48h IS NULL) / COUNT(*), COUNTIF(inr_max_48h IS NOT NULL)
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
UNION ALL SELECT 'platelet_min_48h', COUNT(*), COUNTIF(platelet_min_48h IS NULL), COUNTIF(platelet_min_48h IS NULL) / COUNT(*), COUNTIF(platelet_min_48h IS NOT NULL)
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_inr_missingness_audit` AS
SELECT
    CASE WHEN inr_max_48h IS NULL THEN 1 ELSE 0 END AS inr_missing_48h,
    COUNT(*) AS n,
    COUNTIF(eligible_external_validation = 1) AS primary_validation_eligible_n,
    AVG(CAST(hospital_mortality AS FLOAT64)) AS hospital_mortality_rate,
    AVG(CAST(early_anemia_all AS FLOAT64)) AS early_anemia_rate,
    AVG(CAST(acutephysiologyscore AS FLOAT64)) AS acutephysiologyscore_mean,
    AVG(CAST(apachescore AS FLOAT64)) AS apachescore_mean,
    AVG(CAST(predictedhospitalmortality AS FLOAT64)) AS predictedhospitalmortality_mean
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
GROUP BY inr_missing_48h;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_core_feature_completeness` AS
SELECT
    core_feature_missing_count,
    COUNT(*) AS n,
    COUNT(*) / SUM(COUNT(*)) OVER () AS fraction,
    COUNTIF(hospital_mortality = 1) AS hospital_deaths,
    AVG(CAST(hospital_mortality AS FLOAT64)) AS hospital_mortality_rate
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
GROUP BY core_feature_missing_count;

CREATE OR REPLACE TABLE `mimic-study-498508.eicu_sah_validation.eicu_cohort_flowchart_counts` AS
SELECT '01_sah_candidate_unit_stays' AS step, COUNT(*) AS unit_stays, COUNT(DISTINCT uniquepid) AS patients, 'SAH evidence from diagnosis/admissionDx' AS definition
FROM `mimic-study-498508.eicu_sah_validation.eicu_sah_diagnosis_evidence` dx
INNER JOIN `physionet-data.eicu_crd.patient` p
    ON dx.patientunitstayid = p.patientunitstayid
UNION ALL
SELECT '02_adult', COUNT(*), COUNT(DISTINCT uniquepid), 'age >=18'
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort`
WHERE is_adult = 1
UNION ALL
SELECT '03_non_traumatic', COUNT(*), COUNT(DISTINCT uniquepid), 'exclude traumatic SAH flags'
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort`
WHERE is_adult = 1 AND traumatic_sah_flag = 0
UNION ALL
SELECT '04_first_icu_stay', COUNT(*), COUNT(DISTINCT uniquepid), 'first ICU stay per uniquepid'
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort`
WHERE is_adult = 1 AND traumatic_sah_flag = 0 AND is_first_icu_stay = 1
UNION ALL
SELECT '05_icu_los_ge_24h', COUNT(*), COUNT(DISTINCT uniquepid), 'ICU LOS >=24h'
FROM `mimic-study-498508.eicu_sah_validation.eicu_nsah_cohort`
WHERE eligible_base_cohort = 1
UNION ALL
SELECT '06_core_features_le_2_missing', COUNT(*), COUNT(DISTINCT uniquepid), '8 core features: <=2 missing'
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
WHERE eligible_external_validation = 1
UNION ALL
SELECT '07_icu_los_ge_48h_sensitivity', COUNT(*), COUNT(DISTINCT uniquepid), 'external validation + ICU LOS >=48h'
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
WHERE eligible_external_los48_sensitivity = 1
UNION ALL
SELECT '08_no_rbc_sensitivity', COUNT(*), COUNT(DISTINCT uniquepid), 'external validation + no recorded RBC 0-48h'
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
WHERE eligible_external_no_rbc_sensitivity = 1
UNION ALL
SELECT '09_strict_sah_sensitivity', COUNT(*), COUNT(DISTINCT uniquepid), 'diagnosis table ICD/text SAH evidence, not admissionDx-only'
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
WHERE eligible_external_strict_sah_sensitivity = 1
UNION ALL
SELECT '10_low_missing_sensitivity', COUNT(*), COUNT(DISTINCT uniquepid), '8 core features: <=1 missing'
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
WHERE eligible_external_low_missing_sensitivity = 1
UNION ALL
SELECT '11_complete_case_sensitivity', COUNT(*), COUNT(DISTINCT uniquepid), '8 core features: complete case'
FROM `mimic-study-498508.eicu_sah_validation.eicu_analysis_features_48h`
WHERE eligible_external_complete_case_sensitivity = 1;
