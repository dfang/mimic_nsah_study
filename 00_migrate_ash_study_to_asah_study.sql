-- 将既往 aSAH 研究中已经生成的 BigQuery 中间表从 ash_study 复制到 asah_study。
--
-- 注意：
-- BigQuery 不支持直接重命名 dataset。因此这里采用“新建目标 dataset + 逐表复制”的方式。
-- 运行完成后，旧 dataset `mimic-study-498508.ash_study` 仍会保留；
-- 确认复制无误前不要删除旧 dataset。

DECLARE source_dataset STRING DEFAULT 'ash_study';
DECLARE target_dataset STRING DEFAULT 'asah_study';

CREATE SCHEMA IF NOT EXISTS `mimic-study-498508.asah_study`;

-- 目的：复制旧 ash_study 中所有普通表到 asah_study。
-- 原因：保留上次 aSAH 研究的 cohort 中间结果，同时让后续代码使用更准确的 asah_study 命名。
FOR table_row IN (
    SELECT table_name
    FROM `mimic-study-498508.ash_study.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'BASE TABLE'
    ORDER BY table_name
) DO
    EXECUTE IMMEDIATE FORMAT(
        'CREATE OR REPLACE TABLE `mimic-study-498508.%s.%s` AS SELECT * FROM `mimic-study-498508.%s.%s`',
        target_dataset,
        table_row.table_name,
        source_dataset,
        table_row.table_name
    );
END FOR;

-- 验证：比较源 dataset 与目标 dataset 的表数量。
SELECT
    'dataset_table_count_check' AS check_name,
    (SELECT COUNT(*)
     FROM `mimic-study-498508.ash_study.INFORMATION_SCHEMA.TABLES`
     WHERE table_type = 'BASE TABLE') AS source_base_tables,
    (SELECT COUNT(*)
     FROM `mimic-study-498508.asah_study.INFORMATION_SCHEMA.TABLES`
     WHERE table_type = 'BASE TABLE') AS target_base_tables;

-- 验证：列出目标 dataset 中已复制的表，便于人工核对关键 cohort 表是否存在。
SELECT
    table_name,
    creation_time
FROM `mimic-study-498508.asah_study.INFORMATION_SCHEMA.TABLES`
WHERE table_type = 'BASE TABLE'
ORDER BY table_name;
