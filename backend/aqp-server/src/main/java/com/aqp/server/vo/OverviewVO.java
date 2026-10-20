package com.aqp.server.vo;

/**
 * 数据概览：全部来自 MySQL 统计表实时查询。
 */
public class OverviewVO {

    private int stationCount;
    private int pollutantCount;
    private String startMonth;
    private String endMonth;
    private long pm25ValidSamples;

    public int getStationCount() { return stationCount; }
    public void setStationCount(int stationCount) { this.stationCount = stationCount; }

    public int getPollutantCount() { return pollutantCount; }
    public void setPollutantCount(int pollutantCount) { this.pollutantCount = pollutantCount; }

    public String getStartMonth() { return startMonth; }
    public void setStartMonth(String startMonth) { this.startMonth = startMonth; }

    public String getEndMonth() { return endMonth; }
    public void setEndMonth(String endMonth) { this.endMonth = endMonth; }

    public long getPm25ValidSamples() { return pm25ValidSamples; }
    public void setPm25ValidSamples(long pm25ValidSamples) { this.pm25ValidSamples = pm25ValidSamples; }
}
