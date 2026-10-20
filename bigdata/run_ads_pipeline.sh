#!/bin/bash
# 在 CentOS 虚拟机上执行：重算三张 ADS 结果并合并成单个 CSV
# 用法：bash run_ads_pipeline.sh [/tmp/04_spark_ads.sql]
set -e

SQL_FILE=${1:-/tmp/04_spark_ads.sql}

if [ ! -f "$SQL_FILE" ]; then
  echo "找不到 SQL 文件: $SQL_FILE"
  exit 1
fi

echo "[1/2] Spark SQL 计算并写入 HDFS ..."
spark-sql -f "$SQL_FILE"

echo "[2/2] 合并为单个 CSV ..."
for t in station_pollutant monthly_trend hourly_pattern; do
  hdfs dfs -getmerge "/aq/ads/$t" "/tmp/ads_$t.csv"
  echo "  /tmp/ads_$t.csv  ($(wc -l < /tmp/ads_$t.csv) 行)"
done

echo "完成。把 /tmp/ads_*.csv 拷回 Windows 后执行导入。"
