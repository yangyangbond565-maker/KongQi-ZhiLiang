package com.aqp.server.mapper;

import com.aqp.server.vo.HourlyStatVO;
import com.aqp.server.vo.MonthlyStatVO;
import com.aqp.server.vo.StationStatVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 数据访问层：只读查询三张统计结果表。
 */
@Mapper
public interface StatsMapper {

    @Select("SELECT COUNT(DISTINCT station) FROM ads_station_pollutant")
    int countStations();

    @Select("SELECT COUNT(DISTINCT pollutant) FROM ads_station_pollutant")
    int countPollutants();

    @Select("SELECT MIN(CONCAT(obs_year, '-', LPAD(obs_month, 2, '0'))) FROM ads_monthly_trend")
    String minMonth();

    @Select("SELECT MAX(CONCAT(obs_year, '-', LPAD(obs_month, 2, '0'))) FROM ads_monthly_trend")
    String maxMonth();

    @Select("SELECT IFNULL(SUM(valid_cnt), 0) FROM ads_station_pollutant WHERE pollutant = 'PM2.5'")
    long countPm25Samples();

    @Select("SELECT station, pollutant, avg_value AS avgValue, valid_cnt AS validCnt "
            + "FROM ads_station_pollutant WHERE pollutant = #{pollutant} ORDER BY station")
    List<StationStatVO> selectStationStats(@Param("pollutant") String pollutant);

    @Select("SELECT obs_year AS obsYear, obs_month AS obsMonth, pollutant, "
            + "avg_value AS avgValue, valid_cnt AS validCnt "
            + "FROM ads_monthly_trend WHERE pollutant = #{pollutant} "
            + "ORDER BY obs_year, obs_month")
    List<MonthlyStatVO> selectMonthlyStats(@Param("pollutant") String pollutant);

    @Select("SELECT obs_hour AS obsHour, pollutant, avg_value AS avgValue, valid_cnt AS validCnt "
            + "FROM ads_hourly_pattern WHERE pollutant = #{pollutant} ORDER BY obs_hour")
    List<HourlyStatVO> selectHourlyStats(@Param("pollutant") String pollutant);
}
