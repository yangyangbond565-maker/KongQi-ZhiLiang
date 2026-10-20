USE aq_air;

DROP TABLE IF EXISTS aq_air.ads_station_pollutant;
CREATE EXTERNAL TABLE aq_air.ads_station_pollutant (
  station   STRING COMMENT '站点',
  pollutant STRING COMMENT '污染物',
  avg_value DOUBLE COMMENT '均值（非空样本）',
  valid_cnt INT    COMMENT '有效样本数'
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ("separatorChar" = ",", "quoteChar" = "\"", "escapeChar" = "\\")
STORED AS TEXTFILE
LOCATION '/aq/ads/station_pollutant'
TBLPROPERTIES ("skip.header.line.count" = "1");


DROP TABLE IF EXISTS aq_air.ads_monthly_trend;
CREATE EXTERNAL TABLE aq_air.ads_monthly_trend (
  obs_year  INT    COMMENT '年',
  obs_month INT    COMMENT '月',
  pollutant STRING COMMENT '污染物',
  avg_value DOUBLE COMMENT '月均值',
  valid_cnt INT    COMMENT '有效样本数'
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ("separatorChar" = ",", "quoteChar" = "\"", "escapeChar" = "\\")
STORED AS TEXTFILE
LOCATION '/aq/ads/monthly_trend'
TBLPROPERTIES ("skip.header.line.count" = "1");


DROP TABLE IF EXISTS aq_air.ads_hourly_pattern;
CREATE EXTERNAL TABLE aq_air.ads_hourly_pattern (
  obs_hour  INT    COMMENT '小时 0-23',
  pollutant STRING COMMENT '污染物',
  avg_value DOUBLE COMMENT '小时均值',
  valid_cnt INT    COMMENT '有效样本数'
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ("separatorChar" = ",", "quoteChar" = "\"", "escapeChar" = "\\")
STORED AS TEXTFILE
LOCATION '/aq/ads/hourly_pattern'
TBLPROPERTIES ("skip.header.line.count" = "1");

SELECT 'station' AS t, COUNT(*) AS c FROM aq_air.ads_station_pollutant
UNION ALL SELECT 'monthly', COUNT(*) FROM aq_air.ads_monthly_trend
UNION ALL SELECT 'hourly',  COUNT(*) FROM aq_air.ads_hourly_pattern;

SELECT station, pollutant, avg_value, valid_cnt FROM aq_air.ads_station_pollutant
WHERE station='Changping' AND pollutant='PM2.5';
