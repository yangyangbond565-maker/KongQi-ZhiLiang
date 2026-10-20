# 10 第三步执行记录：Spark SQL 统计与 MySQL 交接

> 日期：2026-10-20　项目：城市空气质量大数据分析与可视化系统
> 方式：Spark 3.3.4 spark-sql → HDFS 结果文件 → MySQL（未走 JDBC，原因见第 2 节）

---

## 1. 连接检查结果

| 检查项 | 结果 |
| --- | --- |
| HDFS / Hive / Spark 服务 | 全部正常，/aq/ods 数据仍在（12 文件 / 32.5 MB） |
| 虚拟机 → Windows MySQL 3306 | 端口可达（TCP 通） |
| JDBC 驱动 | 仅 /opt/software/mysql-connector-java-5.1.49.jar |
| MySQL 账号 | root@'%' 存在，但认证插件为 caching_sha2_password |
| MySQL local_infile | OFF |

**结论：JDBC 不可用。** 5.1.49 驱动不支持 caching_sha2_password，即使网络通也会在认证阶段失败；要修就得换 8.x 驱动或改账号认证方式，两者都属于"改环境/改账号"，按约定没有做。

**实际采用的方式**：Spark SQL 把结果写成 HDFS CSV → 导出到 Windows → 生成 INSERT 脚本 → mysql 客户端导入。这是你事先同意的备用路线。

## 2. 三张统计结果

生成脚本：bigdata/ddl/04_spark_ads.sql（长表结构：维度 + 污染物 + 均值 + 有效样本数）
Hive 映射表：bigdata/ddl/05_hive_ads.sql
HDFS 位置：/aq/ads/station_pollutant、/aq/ads/monthly_trend、/aq/ads/hourly_pattern

| 结果 | 维度 | 行数 | 说明 |
| --- | --- | ---: | --- |
| 站点污染物对比 | station × pollutant | **72** | 12 站 × 6 污染物 |
| 月度趋势 | 年 × 月 × pollutant | **288** | 48 个月 × 6 |
| 小时分布 | 小时 × pollutant | **144** | 24 小时 × 6 |

口径：
- 用 CAST(字段 AS DOUBLE) 把 'NA' 转成 NULL，聚合时自动排除，**缺失值不会被当成 0**；
- 均值只对非空值求平均，同时输出 COUNT(非空) 作为 valid_cnt。

## 3. 校验

| 校验项 | 结果 |
| --- | --- |
| Hive 表行数 | 72 / 288 / 144，与文件行数一致 |
| MySQL 表行数 | 72 / 288 / 144 |
| 抽查：Changping PM2.5 | Spark 71.1 / 34290，MySQL 71.10 / 34290 |
| 抽查：Dongsi PM2.5 | Spark 86.19 / 34314，MySQL 86.19 / 34314 |
| 抽查：2013-07 PM2.5 | 67.91 / 8563（两边一致） |
| 抽查：10 时 PM2.5 | 77.12 / 17162（两边一致） |
| 总量守恒：PM2.5 有效样本 | 按站点求和 412,029 = 按月求和 412,029 = 按小时求和 412,029 = Python 基准 412,029 |

最后一项是有力证据：三个维度独立聚合，总和都等于原始有效样本数，说明没有重复计数、没有漏计。

## 4. MySQL 表

| 表名 | 主键 | 行数 |
| --- | --- | ---: |
| ads_station_pollutant | (station, pollutant) | 72 |
| ads_monthly_trend | (obs_year, obs_month, pollutant) | 288 |
| ads_hourly_pattern | (obs_hour, pollutant) | 144 |

建表语句由 scripts/load_ads_to_mysql.py 生成，只涉及 aq_air 库内新建表，未改动其他库、未改账号。

## 5. 产出文件

- bigdata/ddl/04_spark_ads.sql、05_hive_ads.sql
- scripts/load_ads_to_mysql.py
- data/interim/ads/*.csv（导出结果，可重建）
- data/interim/load_ads.sql（导入脚本，每次重新生成）

## 6. 下一步

第四步：Spring Boot 读取这三张表，提供接口。届时需要为后端准备一个专用数据库账号（不用 root），这属于改账号，会先征得你同意。
