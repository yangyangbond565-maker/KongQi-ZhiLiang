USE aq_air;

DROP VIEW IF EXISTS aq_air.ods_air_raw_v;

CREATE VIEW aq_air.ods_air_raw_v AS
SELECT no, year, month, day, hour, pm25, pm10, so2, no2, co, o3,
       temp, pres, dewp, rain, wd, wspm, station
FROM aq_air.ods_air_raw
WHERE LOWER(no) <> 'no';
