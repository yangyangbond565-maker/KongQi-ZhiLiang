-- 城市空气质量大数据分析与可视化系统
-- ODS 层：原始 CSV 外部表
-- 数据目录：/aq/ods/air_quality（12 个站点 CSV，含表头，缺失值为字面量 NA）
-- 说明：
--   1. 使用 OpenCSVSerde，正确处理字符串字段的双引号（如 "Aotizhongxin"）
--   2. skip.header.line.count=1 跳过每个文件的表头
--   3. 全部字段先按 STRING 读入，保留 NA 原样，不做隐式转换（避免 NA 变成 0）
--   4. 列名 PM2.5 在 Hive 中不合法，统一用 pm25，映射关系见注释

CREATE DATABASE IF NOT EXISTS aq_air
COMMENT '城市空气质量项目库';

USE aq_air;

DROP TABLE IF EXISTS aq_air.ods_air_raw;

CREATE EXTERNAL TABLE aq_air.ods_air_raw (
  no        STRING COMMENT '原始行号，每个文件独立编号',
  year      STRING COMMENT '年',
  month     STRING COMMENT '月',
  day       STRING COMMENT '日',
  hour      STRING COMMENT '小时',
  pm25      STRING COMMENT 'PM2.5 浓度 ug/m3，对应原始列 PM2.5',
  pm10      STRING COMMENT 'PM10 浓度 ug/m3，对应原始列 PM10',
  so2       STRING COMMENT 'SO2 浓度 ug/m3',
  no2       STRING COMMENT 'NO2 浓度 ug/m3',
  co        STRING COMMENT 'CO 浓度 ug/m3',
  o3        STRING COMMENT 'O3 浓度 ug/m3',
  temp      STRING COMMENT '气温 摄氏度，对应原始列 TEMP',
  pres      STRING COMMENT '气压 hPa，对应原始列 PRES',
  dewp      STRING COMMENT '露点 摄氏度，对应原始列 DEWP',
  rain      STRING COMMENT '降水量 mm，对应原始列 RAIN',
  wd        STRING COMMENT '风向',
  wspm      STRING COMMENT '风速 m/s，对应原始列 WSPM',
  station   STRING COMMENT '监测站点'
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  "separatorChar" = ",",
  "quoteChar"     = "\"",
  "escapeChar"    = "\\"
)
STORED AS TEXTFILE
LOCATION '/aq/ods/air_quality'
TBLPROPERTIES ("skip.header.line.count" = "1");

-- 校验：应为 420,768
SELECT COUNT(*) AS total_rows FROM aq_air.ods_air_raw;
