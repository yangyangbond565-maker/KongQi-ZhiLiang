package com.aqp.server.vo;

import java.math.BigDecimal;

public class HourlyStatVO {

    private Integer obsHour;
    private String pollutant;
    private BigDecimal avgValue;
    private Integer validCnt;

    public Integer getObsHour() { return obsHour; }
    public void setObsHour(Integer obsHour) { this.obsHour = obsHour; }

    public String getPollutant() { return pollutant; }
    public void setPollutant(String pollutant) { this.pollutant = pollutant; }

    public BigDecimal getAvgValue() { return avgValue; }
    public void setAvgValue(BigDecimal avgValue) { this.avgValue = avgValue; }

    public Integer getValidCnt() { return validCnt; }
    public void setValidCnt(Integer validCnt) { this.validCnt = validCnt; }
}
