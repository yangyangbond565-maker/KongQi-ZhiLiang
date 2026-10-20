# 09 第二步执行记录：HDFS → Hive → Spark SQL

> 日期：2026-10-20　虚拟机：Hadoop-CentOS7（192.168.20.135）
> 项目：城市空气质量大数据分析与可视化系统

---

## 1. 环境核实（开机后）

| 项 | 实测 |
| --- | --- |
| 系统 | CentOS 7.6.1810，4 vCPU / 7.8 GB / 48 GB 磁盘（可用 43 GB） |
| Hadoop / Hive / Spark | 3.3.6 / 3.1.3 / 3.3.4（均为已有安装，未重装） |
| 运行进程 | NameNode、DataNode、SecondaryNameNode、ResourceManager、NodeManager、JobHistoryServer、Hive Metastore、HiveServer2 |
| HDFS | 容量 47.76 GB，已用 4.48 MB，可用 42.58 GB |
| 既有数据 | /course_b_*、/user/hive/warehouse 下 4 个旧库，**全程未改动** |

## 2. 数据上传

| 步骤 | 命令 | 结果 |
| --- | --- | --- |
| 本地 12 个 CSV | — | 32,508,303 字节 |
| 传到虚拟机 | scp → /tmp/aq_upload | 12 个文件 |
| 建目录 | hdfs dfs -mkdir -p /aq/ods/air_quality | 新建（此前不存在） |
| 上传 | hdfs dfs -put /tmp/aq_upload/*.csv /aq/ods/air_quality/ | 成功 |
| 校验 | hdfs dfs -count /aq/ods/air_quality | **12 个文件 / 32,508,303 字节**，与本地完全一致 |
| 容量 | hdfs dfs -du -s -h | 31.0 M |

## 3. Hive 外部表

建表脚本：bigdata/ddl/01_hive_ods.sql

要点：

- 用 OpenCSVSerde，因为原始 CSV 的字符串字段带双引号（如 "Aotizhongxin"），普通 DELIMITED 会把引号一起读进值里。
- 字段全部按 STRING 读入，缺失标记 NA 原样保留，不做隐式转换，避免被当成 0。
- 原始列名 PM2.5 在 Hive 中不合法，映射为 pm25（其余同理）。

执行结果：

| 检查 | 结果 |
| --- | --- |
| Hive COUNT(*) | **420,768** |
| 每站记录数 | 35,064（抽查 Aotizhongxin / Changping / Dingling） |
| co = 'NA' | 20,701 |
| pm25 = 'NA' | 8,739 |
| 抽样行 | 1, 2013, 3, 1, 0, 4, 300, Aotizhongxin（站点名无引号残留） |

### 3.1 遇到的第一个问题：Spark 多出 12 行

用 Spark SQL 读同一张表，COUNT(*) 得到 **420,780**，正好多 12 行。

原因：skip.header.line.count 是 Hive 执行引擎的属性，**Spark 的扫描不识别**，把每个文件的表头当成了一行数据。Hive 自己查询仍是 420,768，于是两个引擎出现差异。

处理：不改数据、不改预期值，新建视图过滤表头行：

~~~
CREATE VIEW aq_air.ods_air_raw_v AS
SELECT ... FROM aq_air.ods_air_raw
WHERE LOWER(no) <> 'no';
~~~

第一次过滤条件写成 no <> 'no' 无效——表头里的值是 "No"（首字母大写）。改用 LOWER(no) 后，Hive 与 Spark 都返回 420,768。

## 4. Spark SQL 复算

脚本：bigdata/ddl/03_spark_metrics.sql，执行命令 spark-sql -f，Spark master 为 yarn。

| 指标 | Python 基准 | Spark SQL | 是否一致 |
| --- | ---: | ---: | --- |
| 总记录数 | 420,768 | 420,768 | 一致 |
| 站点数 | 12 | 12 | 一致 |
| 每站记录数 | 35,064 | 最小 35,064 / 最大 35,064 | 一致 |
| CO 缺失数 | 20,701 | 20,701 | 一致 |
| PM2.5 均值 | 79.793428 | 79.7934 | 一致（四位小数） |
| PM2.5 有效样本 | 412,029 | 412,029 | 一致 |

## 5. 未完成项：PySpark 脚本

已编写 bigdata/jobs/01_spark_verify.py（含 Hive 读取 + CSV 回退逻辑），但**没有在这台虚拟机上运行成功**。

原因：虚拟机只有 /usr/bin/python2.7，没有 Python 3；PySpark 3.x 不支持 Python 2，python3 命令不存在，脚本无法启动。

没有做的事：没有安装 Python 3，没有升级任何组件，没有改系统配置——等你决定。

因此本次复算实际采用的是 **Spark SQL（spark-sql 命令行）**，不是 PySpark。这一点如实记录，不把 spark-sql 的结果说成 PySpark 的结果。

## 6. 结论

- HDFS 上传、Hive 外部表、Spark SQL 三段链路均已实际跑通，数字与 Python 完全对得上。
- 关键坑有两个：表头在 Spark 中不被跳过；Hive 与 Spark 对同一张表的口径可能不同。已用视图统一。
- 旧数据与旧 Hive 库未被触碰。

## 7. 下一步

1. 决定 PySpark 方案：在虚拟机装 Python 3（yum 或源码），或改用 spark-sql 脚本承担后续清洗与聚合。
2. 进入第三步：把 Spark 统计结果写入 MySQL 的 aq_air 库。
