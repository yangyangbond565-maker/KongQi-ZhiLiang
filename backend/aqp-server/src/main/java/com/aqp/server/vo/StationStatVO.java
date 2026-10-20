package com.aqp.server.vo;

import java.math.BigDecimal;

public class StationStatVO {

    private String station;
    private String pollutant;
    private BigDecimal avgValue;
    private Integer validCnt;

    public String getStation() { return station; }
    public void setStation(String station) { this.station = station; }

    public String getPollutant() { return pollutant; }
    public void setPollutant(String pollutant) { this.pollutant = pollutant; }

    public BigDecimal getAvgValue() { return avgValue; }
    public void setAvgValue(BigDecimal avgValue) { this.avgValue = avgValue; }

    public Integer getValidCnt() { return validCnt; }
    public void setValidCnt(Integer validCnt) { this.validCnt = validCnt; }
}
