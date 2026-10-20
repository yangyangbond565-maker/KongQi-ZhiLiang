package com.aqp.server.service.impl;

import com.aqp.common.BizException;
import com.aqp.server.mapper.StatsMapper;
import com.aqp.server.service.StatsService;
import com.aqp.server.vo.HourlyStatVO;
import com.aqp.server.vo.MonthlyStatVO;
import com.aqp.server.vo.OverviewVO;
import com.aqp.server.vo.StationStatVO;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.List;

@Service
public class StatsServiceImpl implements StatsService {

    /** 当前统计结果中实际存在的污染物 */
    private static final List<String> ALLOWED =
            Arrays.asList("PM2.5", "PM10", "SO2", "NO2", "CO", "O3");

    private final StatsMapper statsMapper;

    public StatsServiceImpl(StatsMapper statsMapper) {
        this.statsMapper = statsMapper;
    }

    private String checkPollutant(String pollutant) {
        String value = (pollutant == null || pollutant.trim().isEmpty())
                ? "PM2.5" : pollutant.trim().toUpperCase();
        if (!ALLOWED.contains(value)) {
            throw new BizException(400, "不支持的污染物：" + pollutant
                    + "，可选：" + String.join(",", ALLOWED));
        }
        return value;
    }

    @Override
    public OverviewVO overview() {
        OverviewVO vo = new OverviewVO();
        vo.setStationCount(statsMapper.countStations());
        vo.setPollutantCount(statsMapper.countPollutants());
        vo.setStartMonth(statsMapper.minMonth());
        vo.setEndMonth(statsMapper.maxMonth());
        vo.setPm25ValidSamples(statsMapper.countPm25Samples());
        return vo;
    }

    @Override
    public List<StationStatVO> stationStats(String pollutant) {
        return statsMapper.selectStationStats(checkPollutant(pollutant));
    }

    @Override
    public List<MonthlyStatVO> monthlyStats(String pollutant) {
        return statsMapper.selectMonthlyStats(checkPollutant(pollutant));
    }

    @Override
    public List<HourlyStatVO> hourlyStats(String pollutant) {
        return statsMapper.selectHourlyStats(checkPollutant(pollutant));
    }
}
