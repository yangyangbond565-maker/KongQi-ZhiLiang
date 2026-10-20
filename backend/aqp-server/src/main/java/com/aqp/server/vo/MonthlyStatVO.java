package com.aqp.server.vo;

import java.math.BigDecimal;

public class MonthlyStatVO {

    private Integer obsYear;
    private Integer obsMonth;
    private String pollutant;
    private BigDecimal avgValue;
    private Integer validCnt;

    public Integer getObsYear() { return obsYear; }
    public void setObsYear(Integer obsYear) { this.obsYear = obsYear; }

    public Integer getObsMonth() { return obsMonth; }
    public void setObsMonth(Integer obsMonth) { this.obsMonth = obsMonth; }

    public String getPollutant() { return pollutant; }
    public void setPollutant(String pollutant) { this.pollutant = pollutant; }

    public BigDecimal getAvgValue() { return avgValue; }
    public void setAvgValue(BigDecimal avgValue) { this.avgValue = avgValue; }

    public Integer getValidCnt() { return validCnt; }
    public void setValidCnt(Integer validCnt) { this.validCnt = validCnt; }
}
