package com.aqp.server.controller;

import com.aqp.common.Result;
import com.aqp.server.service.StatsService;
import com.aqp.server.vo.HourlyStatVO;
import com.aqp.server.vo.MonthlyStatVO;
import com.aqp.server.vo.OverviewVO;
import com.aqp.server.vo.StationStatVO;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 只负责接收请求与返回结果，业务在 Service。
 */
@RestController
@RequestMapping("/api")
public class StatsController {

    private final StatsService statsService;

    public StatsController(StatsService statsService) {
        this.statsService = statsService;
    }

    @GetMapping("/overview")
    public Result<OverviewVO> overview() {
        return Result.ok(statsService.overview());
    }

    @GetMapping("/stations")
    public Result<List<StationStatVO>> stations(
            @RequestParam(value = "pollutant", required = false) String pollutant) {
        return Result.ok(statsService.stationStats(pollutant));
    }

    @GetMapping("/monthly")
    public Result<List<MonthlyStatVO>> monthly(
            @RequestParam(value = "pollutant", required = false) String pollutant) {
        return Result.ok(statsService.monthlyStats(pollutant));
    }

    @GetMapping("/hourly")
    public Result<List<HourlyStatVO>> hourly(
            @RequestParam(value = "pollutant", required = false) String pollutant) {
        return Result.ok(statsService.hourlyStats(pollutant));
    }
}
