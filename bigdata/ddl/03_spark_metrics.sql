USE aq_air;

SELECT COUNT(*) AS total_rows FROM ods_air_raw_v;

SELECT COUNT(DISTINCT station) AS station_count FROM ods_air_raw_v;

SELECT MIN(c) AS min_rows_per_station, MAX(c) AS max_rows_per_station
FROM (SELECT station, COUNT(*) AS c FROM ods_air_raw_v GROUP BY station) t;

SELECT COUNT(*) AS co_missing FROM ods_air_raw_v WHERE co = 'NA';

SELECT ROUND(AVG(CAST(pm25 AS DOUBLE)), 4) AS pm25_avg,
       COUNT(CAST(pm25 AS DOUBLE)) AS pm25_valid
FROM ods_air_raw_v
WHERE pm25 <> 'NA';

SELECT COUNT(*) AS header_rows_still_in_table FROM ods_air_raw WHERE no = 'no';
