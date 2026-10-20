# 07 阶段 2A 执行报告：代理诊断、离线核实与数据获取

> 执行日期：2026-10-20
> 执行范围：只读诊断 + 不改系统网络设置 + 官方数据获取与校验
> 约束：FlClash 保留，未关闭 TUN、未改 DNS/路由/网卡/注册表/防火墙

---

## 1. 结论摘要

| 问题 | 结论 |
| --- | --- |
| FlClash 是否在运行 | **在运行**。界面进程未启动，但代理核心以进程 PID 23448 常驻，监听 7890（代理）与 1053（DNS） |
| 代理节点是否可用 | **可用**。经代理访问 HTTP 返回 200 / 204，Python 经代理访问 UCI 官网返回 200 |
| 为什么之前判断"网络不通" | 当时只用了 curl（Windows Schannel）测试，而该栈在本机 TLS 握手失败；换用 Python（OpenSSL）即成功。**原结论过度概括，特此更正** |
| 能否下载数据 | **能**。已从 UCI 官方源下载并校验，420,768 行全部对上 |
| 是否需要改系统设置 | **不需要**。只在单条命令的进程内设置代理环境变量 |
| 本地 PySpark 能否用 | **能，但有前提**。必须显式指定 spark311 的解释器，否则调用 base 环境的 Python 3.13 会导致 worker 超时 |

---

## 2. 代理诊断（低风险只读）

### 2.1 进程与端口

| 检查项 | 命令 | 结果 |
| --- | --- | --- |
| 进程名匹配 | Get-Process（clash/mihomo/FlClash/verge/sing-box） | 无匹配（进程名不含关键词，或属于服务会话） |
| 安装目录 | Test-Path D:\FlClash | 存在，含 FlClash.exe、FlClashCore.exe、FlClashHelperService.exe、iKuuuVPN.exe |
| 本地监听 | netstat -ano | **127.0.0.1:7890 LISTENING PID 23448**；**0.0.0.0:1053 LISTENING PID 23448**（UDP 也有） |
| 端口归属 | Get-Process -Id 23448 | 无法读取（权限不足，属服务/其他会话） |
| TCP 可达 | Test-NetConnection 127.0.0.1:7890 | True |

**解读**：7890 是 Clash 系混合代理端口，1053 是 DNS 监听端口。两者同属 PID 23448，且该进程无法用当前用户身份读取，符合"FlClash 以系统服务方式运行核心、界面关闭"的情形。

### 2.2 连通性测试（每项只测一次）

| 方式 | 目标 | 结果 |
| --- | --- | --- |
| 直连 | https://archive.ics.uci.edu | 000 / exit 35 / 0.06s |
| 经代理 | https://archive.ics.uci.edu | 000 / exit 35 / 0.003s |
| 经代理 | https://www.baidu.com | 000 / exit 35 / 0.003s |
| 经代理 + --ssl-no-revoke | https://www.baidu.com | 000 / exit 35 |
| 经代理 | **http**://www.baidu.com | **code=200** |
| 经代理 | **http**://cp.cloudflare.com/generate_204 | **code=204** |
| .NET Invoke-WebRequest（经代理） | https://www.baidu.com | 失败："基础连接已经关闭: 接收时发生错误" |
| **Python requests（经代理）** | **https://archive.ics.uci.edu** | **status=200，102,076 字节** |

### 2.3 结论与边界

- **代理核心与节点是通的**：HTTP 200/204 证明出站链路正常；HTTPS 由 Python 打通，证明 TLS 到境外站点也能成功。
- **失败集中在 Windows 的 Schannel / .NET 栈**：curl.exe 与 Invoke-WebRequest 都在 TLS 阶段失败。常见原因是证书吊销检查、企业/安全软件的 TLS 拦截，或该栈未信任某张中间证书。**没有证据指向节点故障或 DNS 配置错误**，因此不对原因下断言。
- **仍需你确认的部分**：FlClash 界面里的节点名称、延迟、流量、规则命中情况，命令行无法读取（未开放外部控制端口）。这部分只能由你在应用界面确认。

### 2.4 采用的通道（不改系统）

只在单条命令内部设置进程级环境变量，命令结束即失效，不写入系统、不写注册表：

~~~
$env:HTTP_PROXY  = "http://127.0.0.1:7890"
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
~~~

该方式已用于数据下载，后续 pip / npm / Maven 也可用同样的按次注入方式（Maven 用 -D 参数，npm 用 --proxy）。

---

## 3. 数据集获取与校验

### 3.1 来源与许可（官方页面实测）

| 项 | 实测内容 |
| --- | --- |
| 页面 | https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data （HTTP 200，105,560 字节） |
| 许可 | Creative Commons Attribution 4.0 International（CC BY 4.0） |
| 引用 | Chen, S. (2017). Beijing Multi-Site Air Quality [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5RK5G |
| 实例数 | 420768 |
| 官方文件 | PRSA2017_Data_20130301-20170228.zip（7.6 MB）、一张 JPG、data.csv、test.csv |
| 下载地址 | https://archive.ics.uci.edu/static/public/501/beijing+multi+site+air+quality+data.zip |

### 3.2 下载与完整性

| 项 | 值 |
| --- | --- |
| 下载文件 | data/raw/archive/PRSA2017_Data_20130301-20170228.zip |
| 字节数 | 8,192,212 |
| SHA-256 | b04da438b2f331ac0ffd45aebdfec0d20d2367feb5f6948c4b1f7ce1191e33c4 |
| zip 完整性 | testzip OK |
| 内层结构 | 内层再套一个同名 zip（7,959,991 字节）+ JPG + data.csv + test.csv |
| 站点文件 | 内层解压后 12 个 CSV，位于 prsa2017/stations/PRSA_Data_20130301-20170228/ |
| 校验清单 | data/raw/checksums-sha256.txt（13 条：1 个压缩包 + 12 个 CSV） |

> 过程备注（如实记录）：第一次解压时把压缩包解到了它自己所在目录，而压缩包里存在同名条目，导致外层包被覆盖成 0 字节。已重新下载并改为解压到独立子目录，第二次校验通过。这是操作失误，不是数据源问题。

### 3.3 数据画像（实测，非推测）

| 指标 | 实测值 |
| --- | --- |
| 文件数 | 12 |
| 每个文件行数 | 35,064（完全一致） |
| 总行数 | **420,768** |
| 字段数 | 18（No + year/month/day/hour + 6 污染物 + 4 气象 + wd/WSPM + station） |
| 站点 | Aotizhongxin、Changping、Dingling、Dongsi、Guanyuan、Gucheng、Huairou、Nongzhanguan、Shunyi、Tiantan、Wanliu、Wanshouxigong（12 个，与任务书一致） |
| 时间范围 | 2013-03-01 00:00 至 2017-02-28 23:00 |
| 站点+时间重复 | **0 条** |
| No 字段范围 | 1 ~ 35064（每文件独立编号，确认不能当全局主键） |
| 缺失标记 | CSV 中为空值（pandas 读为 NaN），非字符串 NA |
| 风向取值 | 16 方位英文缩写（N、NNE、NE、ENE、E、ESE、SE、SSE、S、SSW、SW、WSW、W、WNW、NW、NNW） |

### 3.4 缺失情况（实测）

| 字段 | 缺失数 | 缺失率 |
| --- | --- | --- |
| PM2.5 | 8,739 | 2.08% |
| PM10 | 6,449 | 1.53% |
| SO2 | 9,021 | 2.14% |
| NO2 | 12,116 | 2.88% |
| CO | 20,701 | 4.92% |
| O3 | 13,277 | 3.16% |
| TEMP | 398 | 0.09% |
| PRES | 393 | 0.09% |
| DEWP | 403 | 0.10% |
| RAIN | 390 | 0.09% |
| wd | 1,822 | 0.43% |
| WSPM | 318 | 0.08% |

### 3.5 数值范围与负值

| 字段 | min | 中位数 | P99 | max | 负值数 |
| --- | --- | --- | --- | --- | --- |
| PM2.5 | 2.0 | 55.0 | 370.0 | 999.0 | 0 |
| PM10 | 2.0 | 82.0 | 422.0 | 999.0 | 0 |
| SO2 | 0.286 | 7.0 | 104.0 | 500.0 | 0 |
| NO2 | 1.026 | 43.0 | 157.0 | 290.0 | 0 |
| CO | 100.0 | 900.0 | 6000.0 | 10000.0 | 0 |
| O3 | 0.214 | 45.0 | 245.0 | 1071.0 | 0 |
| TEMP | -19.9 | 14.5 | 33.8 | 41.6 | 64,249（正常） |
| PRES | 982.4 | 1010.4 | 1032.5 | 1042.8 | 0 |
| DEWP | -43.4 | 3.1 | 24.5 | 29.1 | 185,393（正常） |
| RAIN | 0 | 0 | 1.4 | 72.5 | 0 |
| WSPM | 0 | 1.4 | 6.1 | 13.2 | 0 |

### 3.6 单位核验结论（DQ-11 关闭）

官方数据字典原文：

~~~
PM2.5: PM2.5 concentration (ug/m^3)
PM10:  PM10 concentration (ug/m^3)
SO2:   SO2 concentration (ug/m^3)
NO2:   NO2 concentration (ug/m^3)
CO:    CO concentration (ug/m^3)
O3:    O3 concentration (ug/m^3)
TEMP:  temperature (degree Celsius)
PRES:  pressure (hPa)
DEWP:  dew point temperature (degree Celsius)
RAIN:  precipitation (mm)
WSPM:  wind speed (m/s)
~~~

**CO 单位为 μg/m³，不是 mg/m³。** 证据两条且相互印证：

1. 官方字典明确写 ug/m^3；
2. 数值量级：中位数 900、最大 10000。若按 mg/m³ 解读，相当于 0.9~10 g/m³，远超环境浓度，不成立。

因此 03 文档第 3.1 节的"CO 单位待核验"可以关闭。**但六份规划文档本轮未修改**（遵守不覆盖要求），等你确认后我再更新那一条。

### 3.7 新发现的待核查点

| # | 现象 | 为什么需要核查 |
| --- | --- | --- |
| 1 | PM2.5 与 PM10 的 max 都恰好是 999 | 999 可能是真实极值，也可能是某个量程上限/占位值，需看分布尾部与站点分布再定 |
| 2 | SO2 max 恰好 500 | 同上，疑似量程上限 |
| 3 | CO max 恰好 10000 | 同上 |
| 4 | 缺失标记是真空值 | 原设计 DQ-03 假设可能是字符串 NA，实际为真 NaN，规则需简化 |
| 5 | 每站行数完全相同（35,064） | 说明时间网格完整，缺失是"值缺失"不是"行缺失"，DWD 不需要补行 |

这几条不虚构结论，统一记为"阶段二 B 待核查"。

---

## 4. 离线环境核实

| 项 | 实测 | 结论 |
| --- | --- | --- |
| java | 1.8.0_504 (Temurin) | 可用 |
| mvn | 3.6.3，运行在 JDK 8 | 可用 |
| python | 3.13.9（base） | 可用 |
| node / npm | v24.16.0 / 11.13.0 | 可用 |
| git | 2.55.0.windows.3 | 可用 |
| conda | 25.11.1，环境 base + spark311 | 可用 |
| MySQL 服务 | MYSQL80，Running，自动启动，端口 3306 监听 | 服务正常 |
| MySQL 连接 | mysqladmin ping 返回 0；但 SELECT 报 **ERROR 1045 Access denied for user root@localhost (using password: NO)** | **需你提供 root 密码或授权我建专用账号** |
| Maven 本地仓库 | 有 spring-boot / spring-boot-starter-web **2.7.18**；缺 mybatis-plus、mysql-connector、hive-jdbc、lombok | 后端骨架可离线起步，其余需联网拉取 |
| npm 缓存 | 1,280.5 MB（全局）+ 33.8 MB（工作区） | 有缓存，但无法确认是否含 vue/vite |
| pip 缓存 | 1,662.6 MB | 有缓存 |
| Git 仓库 | 工作区尚无 .git | 未初始化 |

### 4.1 PySpark local 模式实测

| 尝试 | 配置 | 结果 |
| --- | --- | --- |
| 1 | 默认（PATH 中的 python 3.13） | SparkSession 28.5 秒建立，但任务阶段 **SocketTimeoutException: Accept timed out**，Python worker 回连失败 |
| 2 | 显式 PYSPARK_PYTHON = spark311\python.exe | **会话 4.8 秒建立；RDD sum = 15；SQL 分组结果正确；Spark 3.5.3** |

**结论**：本机 PySpark 3.5.3 可用，但必须满足：

1. 用 C:\anaconda\envs\spark311\python.exe 启动；
2. 设置 PYSPARK_PYTHON 与 PYSPARK_DRIVER_PYTHON 指向同一解释器；
3. 保留 setLogLevel("ERROR") 以免大量日志干扰。

**已知限制**：日志出现 "Did not find winutils.exe ... HADOOP_HOME and hadoop.home.dir are unset"。这意味着**在 Windows 上写本地文件（Parquet/CSV）可能失败**，本次只做了内存计算，未验证写文件。Windows 端定位为"开发调试"，正式落盘在虚拟机内完成。

---

## 5. 本轮创建与修改的文件

| 路径 | 类型 | 说明 |
| --- | --- | --- |
| data/raw/archive/PRSA2017_Data_20130301-20170228.zip | 新建 | 官方压缩包（8,192,212 字节） |
| data/raw/prsa2017/（内层 zip、JPG、data.csv、test.csv） | 新建 | 官方包内文件 |
| data/raw/prsa2017/stations/PRSA_Data_20130301-20170228/*.csv | 新建 | 12 个站点原始 CSV |
| data/raw/checksums-sha256.txt | 新建 | 13 个文件的 SHA-256 与大小 |
| data/interim/raw_profile.json | 新建 | 数据画像（行数、缺失、分位数、单位说明） |
| docs/07-phase2a-report.md | 新建 | 本文件 |
| docs/01~06 | **未改动** | 遵守不覆盖要求 |

未做：未安装任何软件、未改系统网络设置、未动防火墙、未改 MySQL 账号、未写业务代码。虚拟机在你授权后启动过一次，只读核实完成后已正常关机（见第 6 节）。

---

## 6. 虚拟机只读核实（已完成，已关机）

### 6.1 启动与访问

| 项 | 内容 |
| --- | --- |
| 启动命令 | vmrun -T ws start "D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx" nogui |
| 沙箱限制 | 受限沙箱内 vmrun 报 "vmrun was unable to start"；完整权限下正常（命名管道限制） |
| 来宾 IP | 192.168.20.135（VMnet8，NAT 网段） |
| 登录方式 | ssh -i D:\BigDataLab\ssh\hadoop_vm_rsa root@192.168.20.135 |
| 关机方式 | vmrun stop soft，随后 list 显示 "Total running VMs: 0" |

### 6.2 系统与组件实测

| 项 | 实测 |
| --- | --- |
| 主机名 / 系统 | hadoop / CentOS Linux 7.6.1810 (Core)，内核 3.10.0-957.el7 |
| 资源 | 4 vCPU，7.8 GB 内存，根分区 48 GB（已用 5.2 GB，可用 43 GB） |
| Java | 1.8.0_371，位于 /opt/java（JAVA_HOME 由 /etc/profile.d 设置） |
| Hadoop | **3.3.6**，/opt/hadoop |
| Hive | **3.1.3**，/opt/hive |
| Spark | **3.3.4**（Scala 2.12.15，Java 8），/opt/spark |
| Scala | 独立 scala 命令未安装（随 Spark 自带） |

### 6.3 运行状态（jps + ss 实测）

| 进程 | 端口 | 说明 |
| --- | --- | --- |
| NameNode | 9000（RPC）/ 9870（Web） | HDFS 主节点 |
| DataNode | 9864 / 9866 / 9867 | 数据节点 |
| SecondaryNameNode | 9868 | 检查点 |
| ResourceManager | 8088 / 8030 / 8031 | YARN |
| NodeManager | 8042 / 13562 | YARN 节点 |
| JobHistoryServer | 19888 / 10033 | 历史服务（10033 不是 Hive 端口） |
| Hive Metastore | 9083 | 元数据服务 |
| HiveServer2 | **10000** | 已验证 JDBC：select 1 返回 1 |
| mysqld（虚拟机内） | 3306 | Hive 元数据库 |

### 6.4 配置要点

~~~
spark.master                     yarn
spark.sql.warehouse.dir          /user/hive/warehouse
spark.hadoop.hive.metastore.uris thrift://hadoop:9083
hive.metastore.uris              thrift://hadoop:9083
hive.server2.thrift.port         10000
~~~

### 6.5 现有数据（不会触碰）

| 位置 | 内容 |
| --- | --- |
| HDFS / | course_b_hdfs_*、course_b_hive_export_*、course_b_python_*、/user、/tmp 等 11 项，均为以往课程练习遗留 |
| HDFS 容量 | 47.8 GB 总量，已用 4.5 MB，可用 42.6 GB |
| Hive 数据库 | default、course_b_hive_1788874400、course_b_hive_full_1788876391、course_b_spark_1788874572、doc_demo |
| /user/hive/warehouse | 上述库的目录，未改动 |

**处置原则**：本项目新建 aq_air 库与 /aq 目录，不改动、不删除任何既有目录。

### 6.6 对原设计的修正

| 原假设（04 文档） | 实测 | 处理 |
| --- | --- | --- |
| Spark 3.5.x | 虚拟机为 **3.3.4**（本地 conda 为 3.5.3） | 作业代码以 3.3.4 为准，避免使用 3.4+ 新 API；本地 3.5.3 仅做快速调试 |
| Hive JDBC 只是"理论可行" | HiveServer2 已在 10000 端口运行且 JDBC 实测通过 | 可行性等级提升为"已实测连通"，但仍按原计划作为可选通道 |
| 端口 10000 未确认 | 已确认；10033 属 JobHistoryServer | 端口表更新 |
| 可能存在旧数据 | 确实存在，且不影响新建库 | 只用新命名空间 /aq 与 aq_air |

---

## 7. MySQL 连接与建库

| 项 | 结果 |
| --- | --- |
| 服务 | MYSQL80，Running，自动启动 |
| 版本 | 8.0.42，端口 3306，字符集 utf8mb4 |
| 凭据 | 用户提供的 root 密码验证通过（密码不写入仓库与文档） |
| 已做 | 创建空库 aq_air（utf8mb4_general_ci） |
| 未做 | 未创建/修改任何账号，未改 my.ini 或服务配置 |

> 后续后端建议使用专用账号而非 root，等你在阶段四确认后再建。

---

## 8. Git 初始化

| 项 | 内容 |
| --- | --- |
| 仓库位置 | D:\官方工作区（git init） |
| 忽略规则 | .gitignore：data/raw/*（保留 checksums）、data/interim、.tmp、.tools、.npm-cache、.acl-recovery、target、node_modules、日志等 |
| 首次提交 | 6ecb8dd，9 个文件（6 份阶段一文档 + 本报告 + .gitignore + 校验清单） |
| 作者信息 | 本地仓库级：86701 / 86701@localhost（按"你看着办"暂用系统账号名，随时可改） |
| 修改方式 | git config --local user.name "你的名字"；git config --local user.email "你的邮箱" |

---

## 9. 结论更新（含对阶段一的更正）

| 项 | 阶段一结论 | 本阶段更正 |
| --- | --- | --- |
| 网络 | "整机对外网络不可用" | **过度概括**。HTTP 经代理正常、Python 经代理 HTTPS 正常；仅 curl(Schannel) 与 .NET 栈失败。属于工具栈差异，不是全网故障 |
| 大数据环境 | "Windows 上无组件，虚拟机待核实" | 虚拟机是**完整可用的伪分布式环境**（Hadoop 3.3.6 + Hive 3.1.3 + Spark 3.3.4 + YARN），已开机实测 |
| 数据 | "未下载" | 已下载并校验：420,768 行、12 站点、时间范围与官方一致 |
| CO 单位 | 待核验 | **μg/m³**，官方字典与数值量级双重确认 |
| PySpark | 未验证 | Windows 本地可用，但必须指定 spark311 解释器；写文件受 winutils 缺失限制 |

---

## 10. 仍未完成

| # | 事项 | 阻塞原因 / 前置条件 |
| --- | --- | --- |
| 1 | 极值核查（PM2.5/PM10 = 999、SO2 = 500、CO = 10000） | 需分布与站点维度分析，属阶段二 B |
| 2 | Spark 读写 Hive 表实测 | 需再开机；且要验证 Spark 3.3.4 内置 Hive 2.3.9 与 Hive 3.1.3 metastore 的兼容性 |
| 3 | HDFS 上传 40 MB 数据 | 需开机；空间充足（42.6 GB 可用） |
| 4 | 后端/前端依赖下载 | 网络通道可用，但需按需下载，不建议一次拉全 |
| 5 | 03 文档中 CO 单位条目更新 | 等你确认后我再改，避免"覆盖已有文档" |

---

## 11. 下一步最合适的操作

按依赖顺序，最合理的是先做**数据质量验证（不依赖虚拟机）**，再开机做 HDFS/Hive：

1. 用真实数据跑一遍 DQ-01 ~ DQ-12 规则（Python 本地实现），产出"清洗前后行数、缺失率、重复数、越界数"的真实数字。
2. 核查 999 / 500 / 10000 三个疑似量程上限值的分布。
3. 把结果写成 docs/08-data-quality-report.md，作为阶段三 Spark 作业的对照基准。
4. 再开机：建 /aq 目录 → 上传 CSV → 建 ODS 外部表 → 用 Spark 复算同一批指标，两边数字必须一致。

这样即使虚拟机暂时不开，清洗逻辑也已经被真实数据验证过，Spark 只是"换引擎复算"。

