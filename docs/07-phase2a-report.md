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

未做：未安装任何软件、未改系统网络设置、未动防火墙、未改 MySQL 账号、未启动虚拟机、未写业务代码。

---

## 6. 仍未完成 / 待你确认

| # | 事项 | 需要你做什么 |
| --- | --- | --- |
| 1 | 虚拟机内部版本 | 是否允许我启动 D:\BigDataLab\Hadoop-CentOS7（会占用约 8 GB 内存） |
| 2 | MySQL 账号 | 提供 root 密码，或授权我用现有账号建 aq_air 库与专用用户 |
| 3 | Git 身份 | 提供 name 与 email，我据此初始化仓库并提交第一批文件 |
| 4 | 文档更新 | 是否允许把 03 文档中"CO 单位待核验"更新为已核验（μg/m³） |
| 5 | 999/500/10000 极值 | 阶段二 B 我用分布图和站点分布核查，是否同意 |

---

## 7. 下一步最合适的操作

1. 你确认是否允许启动虚拟机；允许后我做只读核实并关闭。
2. 提供 MySQL 凭据，我建库（只建库与账号，不改服务器配置）。
3. 我用已下载数据做一次"清洗规则验证"（对真实数据跑 DQ 规则，产出清洗前后行数），但**不写入 HDFS**，先在本地验证逻辑。
4. 上述完成后，进入阶段三：HDFS 上传 → Hive 建表 → Spark 清洗聚合。
