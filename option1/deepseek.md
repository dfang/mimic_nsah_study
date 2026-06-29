感谢您的纠正！MIMIC-IV 3.1版本的表名确实变了。下面给出**修正后的完整代码**，将所有`physionet-data.mimiciv_hosp`替换为`physionet-data.mimiciv_3_1_hosp`，`physionet-data.mimiciv_icu`替换为`physionet-data.mimiciv_3_1_icu`。

---

## 修正后的完整数据提取代码（MIMIC-IV 3.1版）

### 第0步：准备工作

```sql
-- 创建您的工作数据集（如果还没有）
CREATE SCHEMA IF NOT EXISTS `mimic-study-498508.ash_study`;
```

### 第1步：提取aSAH患者队列（修正版）

```sql
-- 1.1 查看aSAH对应的ICD编码
SELECT DISTINCT icd_code, long_title
FROM `physionet-data.mimiciv_3_1_hosp.d_icd_diagnoses`
WHERE LOWER(long_title) LIKE '%subarachnoid hemorrhage%'
   OR LOWER(long_title) LIKE '%subarachnoid haemorrhage%'
ORDER BY icd_code;

-- 1.2 提取所有aSAH患者的住院记录（修正版：关联动脉瘤诊断）
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.sah_patients` AS
SELECT DISTINCT
    di.subject_id,
    di.hadm_id,
    a.admittime,
    a.dischtime,
    a.admission_type,
    a.race,
    a.insurance,
    a.hospital_expire_flag
FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di
INNER JOIN `physionet-data.mimiciv_3_1_hosp.admissions` a
    ON di.subject_id = a.subject_id AND di.hadm_id = a.hadm_id
WHERE (di.icd_version = 9 AND di.icd_code LIKE '430%')
   OR (di.icd_version = 10 AND di.icd_code LIKE 'I60%')
-- 关键：确保是动脉瘤性SAH
AND EXISTS (
    SELECT 1 FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` di2
    WHERE di2.subject_id = di.subject_id AND di2.hadm_id = di.hadm_id
    AND ((di2.icd_version = 9 AND di2.icd_code IN ('437.3'))
      OR (di2.icd_version = 10 AND di2.icd_code LIKE 'I67.1%'))
);
```

### 第2步：提取首次ICU停留（修正版）

```sql
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.first_icu_stay` AS
WITH icu_ranked AS (
    SELECT
        ie.subject_id,
        ie.hadm_id,
        ie.stay_id,
        ie.intime AS icu_intime,
        ie.outtime AS icu_outtime,
        ROW_NUMBER() OVER (
            PARTITION BY ie.subject_id, ie.hadm_id
            ORDER BY ie.intime ASC
        ) AS icu_sequence
    FROM `physionet-data.mimiciv_3_1_icu.icustays` ie
    INNER JOIN `mimic-study-498508.ash_study.sah_patients` sp
        ON ie.subject_id = sp.subject_id
       AND ie.hadm_id = sp.hadm_id
)
SELECT
    subject_id,
    hadm_id,
    stay_id,
    icu_intime,
    icu_outtime
FROM icu_ranked
WHERE icu_sequence = 1;
```

### 第3步：提取血红蛋白和贫血时间（修正版）

```sql
-- 3.1 确认Hb的itemid
SELECT itemid, label
FROM `physionet-data.mimiciv_3_1_hosp.d_labitems`
WHERE LOWER(label) LIKE '%hemoglobin%';
-- 确认itemid = 51222

-- 3.2 提取所有Hb测量值
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.hemoglobin_measurements` AS
SELECT
    le.subject_id,
    le.hadm_id,
    le.charttime AS hb_time,
    le.valuenum AS hemoglobin
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON le.subject_id = icu.subject_id
   AND le.hadm_id = icu.hadm_id
WHERE le.itemid = 51222
  AND le.valuenum IS NOT NULL
  AND le.valuenum > 3
  AND le.valuenum < 25
  AND le.charttime >= icu.icu_intime
  AND le.charttime <= icu.icu_outtime;

-- 3.3 找到首次Hb<10的时间（宽松组触发点）
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.first_hb_below_10` AS
SELECT
    subject_id,
    hadm_id,
    MIN(hb_time) AS first_below_10_time,
    MIN(hemoglobin) AS nadir_hb_below_10
FROM `mimic-study-498508.ash_study.hemoglobin_measurements`
WHERE hemoglobin < 10
GROUP BY subject_id, hadm_id;

-- 3.4 找到首次Hb<7的时间（限制组触发点）
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.first_hb_below_7` AS
SELECT
    subject_id,
    hadm_id,
    MIN(hb_time) AS first_below_7_time,
    MIN(hemoglobin) AS nadir_hb_below_7
FROM `mimic-study-498508.ash_study.hemoglobin_measurements`
WHERE hemoglobin < 7
GROUP BY subject_id, hadm_id;

-- 3.5 创建统一的首次贫血时间表（取两者中较早者）
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.first_anemia_time` AS
SELECT
    COALESCE(b10.subject_id, b7.subject_id) AS subject_id,
    COALESCE(b10.hadm_id, b7.hadm_id) AS hadm_id,
    LEAST(
        COALESCE(b10.first_below_10_time, TIMESTAMP('9999-12-31')),
        COALESCE(b7.first_below_7_time, TIMESTAMP('9999-12-31'))
    ) AS first_anemia_time,
    b10.nadir_hb_below_10 AS nadir_hb
FROM `mimic-study-498508.ash_study.first_hb_below_10` b10
FULL OUTER JOIN `mimic-study-498508.ash_study.first_hb_below_7` b7
    ON b10.subject_id = b7.subject_id AND b10.hadm_id = b7.hadm_id;
```

### 第4步：提取输血记录（修正版）

```sql
-- 4.1 确认输血相关itemid
SELECT itemid, label
FROM `physionet-data.mimiciv_3_1_icu.d_items`
WHERE LOWER(label) LIKE '%red blood cell%'
   OR LOWER(label) LIKE '%prbc%';

-- 4.2 提取所有输血事件
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.transfusions` AS
SELECT
    ie.subject_id,
    ie.hadm_id,
    ie.stay_id,
    ie.starttime AS transfusion_time,
    ie.amount,
    ie.amountuom
FROM `physionet-data.mimiciv_3_1_icu.inputevents` ie
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON ie.subject_id = icu.subject_id
   AND ie.hadm_id = icu.hadm_id
   AND ie.stay_id = icu.stay_id
WHERE ie.itemid IN (225795, 226368)
  AND ie.statusdescription != 'Rewritten'
  AND ie.amount > 0;
```

### 第5步：提取生理指标（修正版）

```sql
-- 5.1 MAP的itemid确认
SELECT itemid, label
FROM `physionet-data.mimiciv_3_1_icu.d_items`
WHERE LOWER(label) LIKE '%mean arterial pressure%';

-- 5.2 提取MAP（在首次贫血时间T₀之前）
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.map_baseline` AS
SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime,
    ce.valuenum AS map_value,
    anemia.first_anemia_time
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON ce.subject_id = icu.subject_id AND ce.stay_id = icu.stay_id
INNER JOIN `mimic-study-498508.ash_study.first_anemia_time` anemia
    ON ce.subject_id = anemia.subject_id AND ce.hadm_id = anemia.hadm_id
WHERE ce.itemid IN (220181, 225309)
  AND ce.valuenum IS NOT NULL
  AND ce.valuenum BETWEEN 30 AND 200
  AND ce.charttime < anemia.first_anemia_time
  AND ce.charttime >= icu.icu_intime;

-- 5.3 提取乳酸（在首次贫血时间T₀之前）
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.lactate_baseline` AS
SELECT
    icu.stay_id,
    le.subject_id,
    le.hadm_id,
    le.charttime,
    le.valuenum AS lactate_value,
    anemia.first_anemia_time
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON le.subject_id = icu.subject_id AND le.hadm_id = icu.hadm_id
INNER JOIN `mimic-study-498508.ash_study.first_anemia_time` anemia
    ON le.subject_id = anemia.subject_id AND le.hadm_id = anemia.hadm_id
WHERE le.itemid = 50813
  AND le.valuenum IS NOT NULL
  AND le.valuenum > 0
  AND le.valuenum < 30
  AND le.charttime < anemia.first_anemia_time
  AND le.charttime >= icu.icu_intime;

-- 5.4 提取PaO₂和FiO₂并计算PF比值
-- 5.4.1 提取PaO₂
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.pao2_measurements` AS
SELECT
    le.subject_id,
    le.hadm_id,
    le.charttime AS pao2_time,
    le.valuenum AS pao2,
    anemia.first_anemia_time
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON le.subject_id = icu.subject_id AND le.hadm_id = icu.hadm_id
INNER JOIN `mimic-study-498508.ash_study.first_anemia_time` anemia
    ON le.subject_id = anemia.subject_id AND le.hadm_id = anemia.hadm_id
WHERE le.itemid = 50821
  AND le.valuenum IS NOT NULL
  AND le.valuenum BETWEEN 30 AND 700
  AND le.charttime >= icu.icu_intime
  AND le.charttime < anemia.first_anemia_time;

-- 5.4.2 提取FiO₂
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.fio2_measurements` AS
SELECT
    ce.subject_id,
    ce.hadm_id,
    ce.stay_id,
    ce.charttime AS fio2_time,
    ce.valuenum AS fio2,
    anemia.first_anemia_time
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON ce.subject_id = icu.subject_id AND ce.stay_id = icu.stay_id
INNER JOIN `mimic-study-498508.ash_study.first_anemia_time` anemia
    ON ce.subject_id = anemia.subject_id AND ce.hadm_id = anemia.hadm_id
WHERE ce.itemid = 223835
  AND ce.valuenum IS NOT NULL
  AND ce.valuenum BETWEEN 0.21 AND 1.0
  AND ce.charttime >= icu.icu_intime
  AND ce.charttime < anemia.first_anemia_time;

-- 5.4.3 匹配PaO₂和FiO₂计算PF比值
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.pf_ratio_matched` AS
SELECT
    pa.subject_id,
    pa.hadm_id,
    pa.pao2_time,
    pa.pao2,
    fio2.fio2,
    pa.pao2 / NULLIF(fio2.fio2, 0) AS pf_ratio,
    ABS(TIMESTAMP_DIFF(pa.pao2_time, fio2.fio2_time, MINUTE)) AS time_diff_minutes,
    ROW_NUMBER() OVER (
        PARTITION BY pa.subject_id, pa.hadm_id, pa.pao2_time
        ORDER BY ABS(TIMESTAMP_DIFF(pa.pao2_time, fio2.fio2_time, MINUTE)) ASC
    ) AS rn
FROM `mimic-study-498508.ash_study.pao2_measurements` pa
INNER JOIN `mimic-study-498508.ash_study.fio2_measurements` fio2
    ON pa.subject_id = fio2.subject_id AND pa.hadm_id = fio2.hadm_id
WHERE fio2.fio2_time BETWEEN pa.pao2_time - INTERVAL 4 HOUR
                         AND pa.pao2_time + INTERVAL 1 HOUR;

-- 5.4.4 提取最低PF比值
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.min_pf_ratio` AS
SELECT
    subject_id,
    hadm_id,
    MIN(pf_ratio) AS min_pf_ratio,
    AVG(pf_ratio) AS mean_pf_ratio
FROM `mimic-study-498508.ash_study.pf_ratio_matched`
WHERE rn = 1
  AND pf_ratio > 50
  AND pf_ratio < 600
GROUP BY subject_id, hadm_id;
```

### 第6步：提取患者特征（修正版）

```sql
-- 6.1 人口学特征
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.demographics` AS
SELECT
    p.subject_id,
    p.anchor_age AS age,
    p.gender,
    a.race,
    a.admission_type
FROM `physionet-data.mimiciv_3_1_hosp.patients` p
INNER JOIN `mimic-study-498508.ash_study.sah_patients` sp
    ON p.subject_id = sp.subject_id
INNER JOIN `physionet-data.mimiciv_3_1_hosp.admissions` a
    ON sp.subject_id = a.subject_id AND sp.hadm_id = a.hadm_id;

-- 6.2 初始GCS
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.initial_gcs` AS
WITH gcs_ranked AS (
    SELECT
        ce.subject_id,
        ce.hadm_id,
        ce.stay_id,
        ce.valuenum AS gcs,
        ROW_NUMBER() OVER (
            PARTITION BY ce.stay_id
            ORDER BY ce.charttime ASC
        ) AS rn
    FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
    INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
        ON ce.stay_id = icu.stay_id
    WHERE ce.itemid = 220739
      AND ce.valuenum IS NOT NULL
      AND ce.valuenum BETWEEN 3 AND 15
)
SELECT subject_id, hadm_id, stay_id, gcs AS initial_gcs
FROM gcs_ranked
WHERE rn = 1;

-- 6.3 心率聚合表
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.heart_rate_aggregated` AS
SELECT
    ce.stay_id,
    AVG(ce.valuenum) AS mean_heart_rate,
    MAX(ce.valuenum) AS max_heart_rate,
    MIN(ce.valuenum) AS min_heart_rate
FROM `physionet-data.mimiciv_3_1_icu.chartevents` ce
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON ce.stay_id = icu.stay_id
INNER JOIN `mimic-study-498508.ash_study.first_anemia_time` anemia
    ON ce.subject_id = anemia.subject_id AND ce.hadm_id = anemia.hadm_id
WHERE ce.itemid = 220045
  AND ce.valuenum IS NOT NULL
  AND ce.valuenum BETWEEN 30 AND 200
  AND ce.charttime < anemia.first_anemia_time
  AND ce.charttime >= icu.icu_intime
GROUP BY ce.stay_id;

-- 6.4 休克指数聚合表
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.shock_index_tmp` AS
SELECT
    hr.stay_id,
    hr.charttime,
    hr.valuenum AS heart_rate,
    sbp.valuenum AS sbp,
    hr.valuenum / NULLIF(sbp.valuenum, 0) AS shock_index
FROM `physionet-data.mimiciv_3_1_icu.chartevents` hr
INNER JOIN `physionet-data.mimiciv_3_1_icu.chartevents` sbp
    ON hr.stay_id = sbp.stay_id
   AND hr.charttime = sbp.charttime
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON hr.stay_id = icu.stay_id
INNER JOIN `mimic-study-498508.ash_study.first_anemia_time` anemia
    ON hr.subject_id = anemia.subject_id AND hr.hadm_id = anemia.hadm_id
WHERE hr.itemid = 220045
  AND sbp.itemid = 220179
  AND hr.valuenum IS NOT NULL
  AND sbp.valuenum IS NOT NULL
  AND hr.valuenum BETWEEN 30 AND 200
  AND sbp.valuenum BETWEEN 50 AND 250
  AND hr.charttime < anemia.first_anemia_time
  AND sbp.charttime < anemia.first_anemia_time;

CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.shock_index_aggregated` AS
SELECT
    stay_id,
    MAX(shock_index) AS max_shock_index,
    AVG(shock_index) AS mean_shock_index
FROM `mimic-study-498508.ash_study.shock_index_tmp`
GROUP BY stay_id;

-- 6.5 血小板聚合表
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.platelet_aggregated` AS
SELECT
    icu.stay_id,
    MIN(le.valuenum) AS min_platelet,
    AVG(le.valuenum) AS mean_platelet
FROM `physionet-data.mimiciv_3_1_hosp.labevents` le
INNER JOIN `mimic-study-498508.ash_study.first_icu_stay` icu
    ON le.subject_id = icu.subject_id AND le.hadm_id = icu.hadm_id
INNER JOIN `mimic-study-498508.ash_study.first_anemia_time` anemia
    ON le.subject_id = anemia.subject_id AND le.hadm_id = anemia.hadm_id
WHERE le.itemid = 51265
  AND le.valuenum IS NOT NULL
  AND le.valuenum BETWEEN 10 AND 1000
  AND le.charttime < anemia.first_anemia_time
  AND le.charttime >= icu.icu_intime
GROUP BY icu.stay_id;
```

### 第7步：聚合表创建

```sql
-- MAP聚合表
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.map_aggregated` AS
SELECT
    stay_id,
    MIN(map_value) AS min_map,
    AVG(map_value) AS mean_map
FROM `mimic-study-498508.ash_study.map_baseline`
GROUP BY stay_id;

-- 乳酸聚合表
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.lactate_aggregated` AS
SELECT
    stay_id,
    MAX(lactate_value) AS max_lactate,
    AVG(lactate_value) AS mean_lactate
FROM `mimic-study-498508.ash_study.lactate_baseline`
GROUP BY stay_id;
```

### 第8步：整合最终数据表

```sql
CREATE OR REPLACE TABLE `mimic-study-498508.ash_study.final_cohort` AS
SELECT
    icu.subject_id,
    icu.hadm_id,
    icu.stay_id,
    sp.hospital_expire_flag AS mortality,
    gcs.initial_gcs,
    tg.transfusion_group,
    d.age,
    d.gender,
    d.race,
    d.admission_type,
    map.min_map,
    map.mean_map,
    lac.max_lactate,
    lac.mean_lactate,
    pf.min_pf_ratio,
    anemia.nadir_hb,
    anemia.first_anemia_time,
    hr.mean_heart_rate,
    si.max_shock_index,
    plt.min_platelet
FROM `mimic-study-498508.ash_study.first_icu_stay` icu
LEFT JOIN `mimic-study-498508.ash_study.sah_patients` sp
    ON icu.subject_id = sp.subject_id AND icu.hadm_id = sp.hadm_id
LEFT JOIN `mimic-study-498508.ash_study.initial_gcs` gcs
    ON icu.stay_id = gcs.stay_id
LEFT JOIN `mimic-study-498508.ash_study.demographics` d
    ON icu.subject_id = d.subject_id
LEFT JOIN `mimic-study-498508.ash_study.transfusion_groups_corrected` tg
    ON icu.stay_id = tg.stay_id
LEFT JOIN `mimic-study-498508.ash_study.map_aggregated` map
    ON icu.stay_id = map.stay_id
LEFT JOIN `mimic-study-498508.ash_study.lactate_aggregated` lac
    ON icu.stay_id = lac.stay_id
LEFT JOIN `mimic-study-498508.ash_study.min_pf_ratio` pf
    ON icu.subject_id = pf.subject_id AND icu.hadm_id = pf.hadm_id
LEFT JOIN `mimic-study-498508.ash_study.first_anemia_time` anemia
    ON icu.subject_id = anemia.subject_id AND icu.hadm_id = anemia.hadm_id
LEFT JOIN `mimic-study-498508.ash_study.heart_rate_aggregated` hr
    ON icu.stay_id = hr.stay_id
LEFT JOIN `mimic-study-498508.ash_study.shock_index_aggregated` si
    ON icu.stay_id = si.stay_id
LEFT JOIN `mimic-study-498508.ash_study.platelet_aggregated` plt
    ON icu.stay_id = plt.stay_id
WHERE tg.transfusion_group IS NOT NULL;
```

### 第9步：验证数据

```sql
-- 检查最终表
SELECT COUNT(*) AS total_patients FROM `mimic-study-498508.ash_study.final_cohort`;

SELECT
    COUNT(*) AS total,
    COUNTIF(min_map IS NOT NULL) AS map_ok,
    COUNTIF(max_lactate IS NOT NULL) AS lactate_ok,
    COUNTIF(min_pf_ratio IS NOT NULL) AS pf_ok,
    COUNTIF(initial_gcs IS NOT NULL) AS gcs_ok,
    COUNTIF(transfusion_group = 1) AS liberal_group,
    COUNTIF(transfusion_group = 0) AS restrictive_group
FROM `mimic-study-498508.ash_study.final_cohort`;
```

---

## 表名对照汇总

| 原表名（MIMIC-IV v2.x）       | 新表名（MIMIC-IV v3.1）           |
| ----------------------------- | --------------------------------- |
| `physionet-data.mimiciv_hosp` | `physionet-data.mimiciv_3_1_hosp` |
| `physionet-data.mimiciv_icu`  | `physionet-data.mimiciv_3_1_icu`  |
| `physionet-data.mimiciv_ed`   | `physionet-data.mimiciv_3_1_ed`   |

---

## Python建模部分

建模代码中的表名不需要修改，因为您只需要导入最终生成的CSV文件。建模代码保持不变。

需要我把Python建模代码也重新发一遍吗（保持原样即可）？
