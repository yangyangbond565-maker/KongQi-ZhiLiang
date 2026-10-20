# 城市空气质量大数据分析与可视化系统

数据科学与大数据技术专业综合实训项目。以 UCI 北京市多站点空气质量历史数据为基础，完成
HDFS 存储 → Hive 建表 → Spark SQL 统计 → MySQL 落库 → Spring Boot 接口 → Vue3 大屏 的完整链路。

---

## 1. 项目简介

- 数据来源：UCI Machine Learning Repository，Beijing Multi-Site Air Quality Data Set（ID 501）
- 数据规模：420,768 条小时级记录，12 个监测站点，2013-03 至 2017-02
- 项目定位：课程综合实训，单机伪分布式环境，不是生产系统
- 注意：数据是历史数据，页面不提供实时监测，也不计算 AQI

## 2. 主要功能

| 模块 | 内容 |
| --- | --- |
| 数据质量检查 | Python 统计总行数、站点数、缺失率、重复记录、异常值与特殊值分布 |
| 大数据处理 | HDFS 存原始数据，Hive 建外部表，Spark SQL 生成三张统计结果 |
| 数据交接 | 统计结果导出 CSV，导入 MySQL 的 aq_air 库 |
| 后端接口 | 4 个只读接口：概览、站点对比、月度趋势、小时分布 |
| 可视化大屏 | 指标卡 + 站点柱状图 + 月度折线 + 24 小时折线，可切换污染物 |
| 统计查询页 | 站点 / 月度 / 小时三张表，带分页，可切换污染物 |
| 独立分析图 | Python + Matplotlib 生成 6 张静态图（站点、月度、小时、缺失率、季节、相关性），并自动核对关键数值 |

## 3. 技术栈

Windows 侧：JDK 8、Maven 3.6.3、Spring Boot 2.7.18、MyBatis、MySQL 8.0、Node.js 24、Vue 3.5、Vite 5、ECharts 5.5、Python 3.13（pandas / matplotlib）

虚拟机侧：CentOS 7.6、Hadoop 3.3.6、Hive 3.1.3、Spark 3.3.4（spark-sql）

## 4. 数据处理流程

~~~
UCI 官方 CSV
   │  上传
   ▼
HDFS /aq/ods/air_quality        （12 个站点 CSV，原始层）
   │  Hive 外部表 aq_air.ods_air_raw + 视图 ods_air_raw_v（过滤表头）
   ▼
Spark SQL（bigdata/ddl/04_spark_ads.sql）
   │
   ├─► HDFS /aq/ads/station_pollutant   站点 × 污染物   72 行
   ├─► HDFS /aq/ads/monthly_trend       年月 × 污染物   288 行
   └─► HDFS /aq/ads/hourly_pattern      小时 × 污染物   144 行
   │  导出 CSV（脚本 getmerge）
   ▼
Windows：data/interim/ads/*.csv → scripts/load_ads_to_mysql.py 生成 INSERT
   ▼
MySQL aq_air 三张表 → Spring Boot（MyBatis） → REST /api → Vue3 页面
~~~

**重要**：重算后的结果需要手工从虚拟机拷回 Windows 再导入，当前不是全自动流水线。

## 5. 目录结构

~~~
D:\官方工作区\
├── backend\                 Maven 父工程（Spring Boot 2.7.18）
│   ├── pom.xml
│   ├── aqp-common\          统一返回 Result、业务异常
│   ├── aqp-server\          Controller / Service / Mapper / VO / 配置
│   ├── run-backend.ps1      读取 .env.local 并启动 jar
│   └── .env.local           本地数据库口令（已 gitignore，不入库）
├── frontend\                Vue3 + Vite
│   └── src\views\           Dashboard.vue、Query.vue
├── bigdata\
│   ├── ddl\                 Hive 建表、Spark SQL 统计脚本
│   ├── jobs\                01_spark_verify.py（当时 PySpark 未跑通，留作参考）
│   └── run_ads_pipeline.sh  虚拟机上重算并合并 CSV
├── scripts\
│   ├── data_quality_check.py
│   └── load_ads_to_mysql.py
├── analysis\
│   ├── matplotlib_charts.py   6 张分析图脚本（可重复运行）
│   └── output\                生成的 PNG 与底表 CSV
├── data\                    原始数据与中间结果（已 gitignore）
├── docs\                    各阶段记录
└── README.md
~~~

## 6. 已验证的软件环境

| 组件 | 版本 | 位置 |
| --- | --- | --- |
| 操作系统 | Windows 11 26200 | 本机 |
| JDK | 1.8.0_504（Temurin） | C:\Program Files\Eclipse Adoptium |
| Maven | 3.6.3 | D:\maven |
| MySQL | 8.0.42 | D:\MYSQL |
| Node.js / npm | 24.16.0 / 11.13.0 | D:\Node.js |
| Python | 3.13.9（Anaconda） | C:\anaconda |
| 虚拟机 | CentOS 7.6.1810 | D:\BigDataLab\Hadoop-CentOS7 |
| Hadoop / Hive / Spark | 3.3.6 / 3.1.3 / 3.3.4 | /opt 下 |

虚拟机 IP 示例：192.168.20.135（NAT，VMnet8），SSH 私钥 D:\BigDataLab\ssh\hadoop_vm_rsa。

## 7. 数据集来源与版权

- 名称：Beijing Multi-Site Air Quality Data Set
- 发布：UCI Machine Learning Repository，DOI 10.24432/C5RK5G
- 地址：https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data
- 许可：CC BY 4.0，使用时需注明来源
- 引用：Chen, S. (2017). Beijing Multi-Site Air Quality [Dataset]. UCI Machine Learning Repository.
- 单位以官方数据字典为准：PM2.5/PM10/SO2/NO2/CO/O3 均为 μg/m³，温度 ℃，气压 hPa，风速 m/s，降水 mm

## 8. 启动后端（Windows）

首次准备（只需一次）：

~~~powershell
cd D:\官方工作区\backend
mvn -DskipTests package
~~~

在 backend\.env.local 中写入口令（该文件不入库）：

~~~
AQ_DB_USER=aq_user
AQ_DB_PASSWORD=你的密码
~~~

启动：

~~~powershell
cd D:\官方工作区\backend
powershell -ExecutionPolicy Bypass -File .\run-backend.ps1
~~~

看到 Started AqpServerApplication 即成功，端口 8080。

> 构建时 Maven 需要写入本地仓库 D:\install\maven\repostory（在工作区之外）。

## 9. 启动前端（Windows）

~~~powershell
cd D:\官方工作区\frontend
npm install
npm run dev
~~~

访问 http://localhost:5173/ 。Vite 已配置代理：/api → http://127.0.0.1:8080。

## 10. 虚拟机与数据重算

### 10.1 启动虚拟机

用 VMware Workstation 打开 D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx 启动，或用命令行：

~~~powershell
& 'D:\VMware\vmrun.exe' -T ws start 'D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx' nogui
& 'D:\VMware\vmrun.exe' -T ws getGuestIPAddress 'D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx' -wait
~~~

开机后确认服务：

~~~bash
jps          # 应有 NameNode、DataNode、ResourceManager、NodeManager、RunJar（Hive）
hdfs dfs -ls /aq/ods/air_quality
~~~

### 10.2 重算三张统计结果

~~~powershell
# 1) 把 SQL 和脚本传到虚拟机
scp -i D:\BigDataLab\ssh\hadoop_vm_rsa bigdata\ddl\04_spark_ads.sql root@192.168.20.135:/tmp/
scp -i D:\BigDataLab\ssh\hadoop_vm_rsa bigdata\run_ads_pipeline.sh root@192.168.20.135:/tmp/
~~~

~~~bash
# 2) 在虚拟机上执行（Spark SQL 计算 + getmerge 合并 CSV）
bash /tmp/run_ads_pipeline.sh /tmp/04_spark_ads.sql
~~~

预期输出行数：stations 73 行、monthly 289 行、hourly 145 行（含表头，数据行分别为 72 / 288 / 144）。

### 10.3 结果传回 Windows 并更新 MySQL

~~~powershell
# 3) 拷回三个 CSV
foreach ($n in 'station_pollutant','monthly_trend','hourly_pattern') {
  scp -i D:\BigDataLab\ssh\hadoop_vm_rsa "root@192.168.20.135:/tmp/ads_$n.csv" "D:\官方工作区\data\interim\ads\ads_$n.csv"
}

# 4) 生成导入脚本（会重新读取三个 CSV）
cd D:\官方工作区
python scripts\load_ads_to_mysql.py

# 5) 执行导入（需要可写账号，例如 root）
Get-Content .\data\interim\load_ads.sql -Encoding UTF8 | & 'D:\MYSQL\bin\mysql.exe' -u root -p --default-character-set=utf8mb4
~~~

注意：导入脚本只对 aq_air 库内的三张 ADS 表执行 DROP TABLE IF EXISTS 后重建，
不会影响其他库（如 course_b_*、gdpolicyrag 等）。

## 11. 前端访问地址与页面

| 地址 | 页面 |
| --- | --- |
| http://localhost:5173/#/ | 数据大屏：4 个指标卡 + 站点柱状图 + 月度折线 + 24 小时折线 |
| http://localhost:5173/#/query | 统计查询：站点 / 月度 / 小时三张表，支持分页 |

两个页面右上角均可切换污染物：PM2.5、PM10、SO2、NO2、CO、O3。

## 12. 后端接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/overview | 站点数、污染物数、起止月份、PM2.5 有效样本数 |
| GET | /api/stations?pollutant=PM2.5 | 各站点平均浓度与有效样本数 |
| GET | /api/monthly?pollutant=PM2.5 | 月度平均浓度与有效样本数 |
| GET | /api/hourly?pollutant=PM2.5 | 各小时平均浓度与有效样本数 |

返回格式：{"code":0,"message":"ok","data":...}。

## 13. 常见问题

| 问题 | 处理 |
| --- | --- |
| 8080 端口被占用 | 用 netstat -ano 找到 :8080 对应的 PID，结束进程或改端口 |
| 后端启动报数据源错误 | 确认 MySQL80 服务已启动，且 .env.local 中的口令正确 |
| 页面提示无法连接后端服务 | 后端未启动，或 Vite 代理指向的端口不是 8080 |
| 页面能开但没有数据 | 检查三张表是否有数据：SELECT COUNT(*) FROM aq_air.ads_station_pollutant; |
| npm install 报 EPERM | 指定工作区内缓存：npm install --cache "D:\官方工作区\.npm-cache" |
| 控制台中文乱码 | PowerShell 终端编码问题，不影响浏览器显示 |
| 不想开虚拟机也想看页面 | 可以，页面只依赖 MySQL 里已有的统计结果 |

## 14. 停止服务

| 服务 | 停止方式 |
| --- | --- |
| 后端 | 运行窗口按 Ctrl+C，或 taskkill /PID 进程号 /F |
| 前端 | 运行窗口按 Ctrl+C，或结束对应 node 进程 |
| 虚拟机 | & 'D:\VMware\vmrun.exe' -T ws stop 'D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx' soft |

## 15. 当前未完成事项

- 数据重算到 MySQL 仍是手工拷文件 + 手工导入，没有做一键自动化。
- PySpark 未运行：虚拟机只有 Python 2.7，项目改用 spark-sql 完成统计。
- 没有单元测试与自动化测试，验证方式为手工核对。
- 前端 ECharts 为全量引入，构建包偏大（超过 500 kB），未做按需加载。
- 未实现 AQI 计算、实时监测、地图、登录权限（按项目范围明确不做）。
