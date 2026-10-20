-- 第三步：Spark SQL 生成三张 ADS 统计结果（长表：维度 + 污染物 + 均值 + 有效样本数）
-- 口径：CAST('NA' AS DOUBLE) 得到 NULL，聚合时自动排除，缺失值不会被当成 0
USE aq_air;

CREATE OR REPLACE TEMPORARY VIEW aq_long AS
SELECT station,
       CAST(year AS INT)  AS obs_year,
       CAST(month AS INT) AS obs_month,
       CAST(hour AS INT)  AS obs_hour,
       'PM2.5' AS pollutant,
       CAST(pm25 AS DOUBLE) AS value
FROM aq_air.ods_air_raw_v
UNION ALL
SELECT station,
       CAST(year AS INT)  AS obs_year,
       CAST(month AS INT) AS obs_month,
       CAST(hour AS INT)  AS obs_hour,
       'PM10' AS pollutant,
       CAST(pm10 AS DOUBLE) AS value
FROM aq_air.ods_air_raw_v
UNION ALL
SELECT station,
       CAST(year AS INT)  AS obs_year,
       CAST(month AS INT) AS obs_month,
       CAST(hour AS INT)  AS obs_hour,
       'SO2' AS pollutant,
       CAST(so2 AS DOUBLE) AS value
FROM aq_air.ods_air_raw_v
UNION ALL
SELECT station,
       CAST(year AS INT)  AS obs_year,
       CAST(month AS INT) AS obs_month,
       CAST(hour AS INT)  AS obs_hour,
       'NO2' AS pollutant,
       CAST(no2 AS DOUBLE) AS value
FROM aq_air.ods_air_raw_v
UNION ALL
SELECT station,
       CAST(year AS INT)  AS obs_year,
       CAST(month AS INT) AS obs_month,
       CAST(hour AS INT)  AS obs_hour,
       'CO' AS pollutant,
       CAST(co AS DOUBLE) AS value
FROM aq_air.ods_air_raw_v
UNION ALL
SELECT station,
       CAST(year AS INT)  AS obs_year,
       CAST(month AS INT) AS obs_month,
       CAST(hour AS INT)  AS obs_hour,
       'O3' AS pollutant,
       CAST(o3 AS DOUBLE) AS value
FROM aq_air.ods_air_raw_v;

-- 1. 站点 × 污染物
INSERT OVERWRITE DIRECTORY '/aq/ads/station_pollutant'
USING csv OPTIONS ('header' = 'true')
SELECT /*+ COALESCE(1) */ station, pollutant,
       ROUND(AVG(value), 2) AS avg_value,
       COUNT(value)         AS valid_cnt
FROM aq_long
GROUP BY station, pollutant;

-- 2. 年月 × 污染物
INSERT OVERWRITE DIRECTORY '/aq/ads/monthly_trend'
USING csv OPTIONS ('header' = 'true')
SELECT /*+ COALESCE(1) */ obs_year, obs_month, pollutant,
       ROUND(AVG(value), 2) AS avg_value,
       COUNT(value)         AS valid_cnt
FROM aq_long
GROUP BY obs_year, obs_month, pollutant;

-- 3. 小时 × 污染物
INSERT OVERWRITE DIRECTORY '/aq/ads/hourly_pattern'
USING csv OPTIONS ('header' = 'true')
SELECT /*+ COALESCE(1) */ obs_hour, pollutant,
       ROUND(AVG(value), 2) AS avg_value,
       COUNT(value)         AS valid_cnt
FROM aq_long
GROUP BY obs_hour, pollutant;
