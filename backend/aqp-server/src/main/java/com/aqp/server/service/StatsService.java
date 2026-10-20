package com.aqp.server.service;

import com.aqp.server.vo.HourlyStatVO;
import com.aqp.server.vo.MonthlyStatVO;
import com.aqp.server.vo.OverviewVO;
import com.aqp.server.vo.StationStatVO;

import java.util.List;

public interface StatsService {

    OverviewVO overview();

    List<StationStatVO> stationStats(String pollutant);

    List<MonthlyStatVO> monthlyStats(String pollutant);

    List<HourlyStatVO> hourlyStats(String pollutant);
}
