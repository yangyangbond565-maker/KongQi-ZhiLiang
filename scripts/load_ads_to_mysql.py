# -*- coding: utf-8 -*-
"""
把 Spark SQL 导出的三张 ADS 结果 CSV 转换成 MySQL 导入脚本。

背景：虚拟机里的 JDBC 驱动是 mysql-connector-java 5.1.49，
而 MySQL 8.0 的账号使用 caching_sha2_password，驱动不支持；
同时 local_infile 为 OFF。因此采用"导出 CSV + 生成 INSERT"的方式导入。

输出：data/interim/load_ads.sql（只含 DDL 与 INSERT，不含任何账号密码）
"""
import csv
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "data", "interim", "ads")
OUT = os.path.join(BASE, "data", "interim", "load_ads.sql")

TABLES = [
    {
        "name": "ads_station_pollutant",
        "file": "ads_station_pollutant.csv",
        "ddl": """CREATE TABLE ads_station_pollutant (
  station   VARCHAR(64)  NOT NULL COMMENT '监测站点',
  pollutant VARCHAR(16)  NOT NULL COMMENT '污染物',
  avg_value DECIMAL(10,2) NULL    COMMENT '均值(仅非空样本)',
  valid_cnt INT          NOT NULL COMMENT '有效样本数',
  PRIMARY KEY (station, pollutant)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站点污染物对比';""",
        "cols": ["station", "pollutant", "avg_value", "valid_cnt"],
    },
    {
        "name": "ads_monthly_trend",
        "file": "ads_monthly_trend.csv",
        "ddl": """CREATE TABLE ads_monthly_trend (
  obs_year  SMALLINT     NOT NULL COMMENT '年',
  obs_month TINYINT      NOT NULL COMMENT '月',
  pollutant VARCHAR(16)  NOT NULL COMMENT '污染物',
  avg_value DECIMAL(10,2) NULL    COMMENT '月均浓度',
  valid_cnt INT          NOT NULL COMMENT '有效样本数',
  PRIMARY KEY (obs_year, obs_month, pollutant)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月度趋势';""",
        "cols": ["obs_year", "obs_month", "pollutant", "avg_value", "valid_cnt"],
    },
    {
        "name": "ads_hourly_pattern",
        "file": "ads_hourly_pattern.csv",
        "ddl": """CREATE TABLE ads_hourly_pattern (
  obs_hour  TINYINT      NOT NULL COMMENT '小时 0-23',
  pollutant VARCHAR(16)  NOT NULL COMMENT '污染物',
  avg_value DECIMAL(10,2) NULL    COMMENT '小时均值',
  valid_cnt INT          NOT NULL COMMENT '有效样本数',
  PRIMARY KEY (obs_hour, pollutant)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小时分布';""",
        "cols": ["obs_hour", "pollutant", "avg_value", "valid_cnt"],
    },
]


def sql_literal(value, numeric):
    if value is None or value == "":
        return "NULL"
    if numeric:
        return str(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def main():
    lines = ["USE aq_air;", ""]
    for t in TABLES:
        path = os.path.join(SRC, t["file"])
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        lines.append("DROP TABLE IF EXISTS %s;" % t["name"])
        lines.append(t["ddl"])
        lines.append("")

        cols = t["cols"]
        numeric = {"avg_value", "valid_cnt", "obs_year", "obs_month", "obs_hour"}
        batch = []
        for r in rows:
            vals = ", ".join(sql_literal(r.get(c), c in numeric) for c in cols)
            batch.append("(" + vals + ")")
        lines.append("INSERT INTO %s (%s) VALUES" % (t["name"], ", ".join(cols)))
        lines.append(",\n".join(batch) + ";")
        lines.append("")
        print("%-24s rows=%d" % (t["name"], len(rows)))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
