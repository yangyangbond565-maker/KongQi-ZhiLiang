# 11 第四步执行记录：只读账号与 Spring Boot 后端

> 日期：2026-10-20　项目：城市空气质量大数据分析与可视化系统

---

## 1. 只读数据库账号 aq_user

| 项 | 内容 |
| --- | --- |
| 账号 | aq_user@localhost、aq_user@127.0.0.1（仅本机） |
| 口令 | 15 位强随机串，存放于 backend/.env.local（已被 .gitignore 忽略，不在仓库内） |
| 全局权限 | 仅 USAGE（等于无权限） |
| 表权限 | SELECT：ads_station_pollutant、ads_monthly_trend、ads_hourly_pattern |

权限验证（实测）：

| 操作 | 结果 |
| --- | --- |
| 查三张表 | 成功：72 / 288 / 144 行 |
| UPDATE | 拒绝：ERROR 1142 UPDATE command denied |
| DROP TABLE | 拒绝：ERROR 1142 DROP command denied |
| 查 mysql.user | 拒绝：ERROR 1142 SELECT command denied |
| 执行后表结构 | 完好，行数未变 |

未修改 root、未改认证方式、未改服务器配置。

## 2. 数据重算流程（可重复执行）

1. 启动虚拟机，确认 HDFS/Hive/Spark 正常。
2. 把 bigdata/ddl/04_spark_ads.sql 拷到虚拟机，执行：
   bash bigdata/run_ads_pipeline.sh /tmp/04_spark_ads.sql
   该脚本会跑 Spark SQL 并把三个结果目录合并成 /tmp/ads_*.csv。
3. 把三个 CSV 拷回 D:\官方工作区\data\interim\ads\。
4. 生成并执行导入脚本：
   python scripts/load_ads_to_mysql.py
   （生成 data/interim/load_ads.sql，再用 mysql 客户端执行，需要可写账号）

说明：MySQL 的 local_infile 为 OFF，虚拟机的 JDBC 驱动 5.1.49 不支持 caching_sha2_password，所以仍采用"导 CSV + INSERT"的方式，不走 JDBC。

## 3. Spring Boot 后端

工程结构（Maven 父子）：

~~~
backend/pom.xml                父工程，Spring Boot 2.7.18，JDK 8
backend/aqp-common/            统一返回 Result、业务异常 BizException
backend/aqp-server/            启动类、Controller、Service、Mapper、VO、配置
~~~

分层：

- Controller（StatsController）：只接收请求、调用 Service、返回 Result
- Service（StatsService / StatsServiceImpl）：校验污染物参数（白名单），组装结果
- Mapper（StatsMapper）：MyBatis 注解写 SQL，只读三张表

接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/overview | 站点数、污染物数、起止月份、PM2.5 有效样本总数 |
| GET | /api/stations?pollutant=PM2.5 | 各站点均值与有效样本数 |
| GET | /api/monthly?pollutant=PM2.5 | 48 个月的均值与样本数 |
| GET | /api/hourly?pollutant=PM2.5 | 0-23 时的均值与样本数 |

统一返回：{"code":0,"message":"ok","data":...}；参数非法返回 code=400；数据库异常返回 code=500。

## 4. 配置文件与启动

application.yml 中的数据库口令写成占位符 \${AQ_DB_PASSWORD}，不落库。

启动方式（Windows）：

~~~
cd backend
mvn -DskipTests package
powershell -File .\run-backend.ps1
~~~

run-backend.ps1 会读取 .env.local 里的 AQ_DB_PASSWORD，再启动 jar。

## 5. 实际测试结果

服务启动：Tomcat 8080，Started AqpServerApplication in 2.26 seconds。

| 接口 | 返回 |
| --- | --- |
| /api/overview | stationCount=12，pollutantCount=6，2013-03 ~ 2017-02，pm25ValidSamples=412029 |
| /api/stations?pollutant=PM2.5 | 12 条，首条 Aotizhongxin 82.77 / 34139，末条 Wanshouxigong 85.02 / 34368 |
| /api/monthly?pollutant=PM2.5 | 48 条，首条 2013-03 = 104.89 / 8881，末条 2017-02 = 69.31 / 7842 |
| /api/hourly?pollutant=PM2.5 | 24 条，10 时 = 77.12 / 17162 |
| /api/stations?pollutant=ABC | code=400，提示可选污染物 |
| /api/stations?pollutant=SO2 | 12 条，首条 Aotizhongxin 17.38 / 34129 |

连接检查：information_schema.processlist 显示数据库连接全部是 aq_user，没有使用 root。

## 6. 已知问题

- 构建时 Maven 需要写入 D:\install\maven\repostory（工作区之外），在受限沙箱下会失败，需要允许其写入本地仓库。
- 接口中文提示在 PowerShell 控制台显示为乱码，属于终端编码问题，JSON 内容本身是 UTF-8。
- 尚未做单元测试与接口自动化测试，仅做了手工调用验证。
- 前端未开发。

## 7. 下一步

第五步：Vue3 大屏，调用这四个接口。
