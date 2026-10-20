# 04 系统架构设计

> 文档版本：v0.1（阶段一）
> 关联文档：02-requirements.md（需求编号）、03-data-dictionary.md（表结构）、05-environment-audit.md（环境约束）
> 说明：本文所有版本号均为"设计目标"，实际版本以阶段二核实结果为准。

---

## 1. 设计目标与约束

设计这套架构时要同时满足三件事，它们有时互相冲突：

| 目标 | 来源 | 对架构的影响 |
| --- | --- | --- |
| 完整覆盖课程技术栈 | 任务书第三节 | 必须真的用 HDFS、Hive、Spark SQL、Maven、Spring Boot、Vue3、Matplotlib |
| 环境能跑起来 | 本机实际情况 | 大数据组件只能装在 Linux 虚拟机里；Windows 上只有 JDK/Python/Node |
| 答辩时不能掉链子 | 演示场景 | 页面数据不能依赖"虚拟机此刻是否开机" |

第三条是最容易被忽视的：如果大屏每个数字都实时查 Hive，那么虚拟机一挂、HiveServer2 延迟一高，答辩现场就是白屏。所以架构上必须**把"计算"和"展示"解耦**。

---

## 2. 总体架构图

~~~mermaid
flowchart TD
    subgraph L1["① 数据来源层"]
        A1["UCI 官方 CSV<br/>12 站点 × 4 年<br/>约 42 万行"]
    end

    subgraph L2["② 大数据存储层（CentOS7 虚拟机内）"]
        B1[("HDFS /aq/ods<br/>原始 CSV 只读")]
        B2[("HDFS /aq/dwd<br/>清洗后 Parquet")]
        B3[("HDFS /aq/ads<br/>聚合结果 Parquet")]
        C1["Hive Metastore<br/>外部表映射 + SQL 查询"]
    end

    subgraph L3["③ 大数据计算层（虚拟机内）"]
        D1["Spark SQL 作业1<br/>清洗与质量标记"]
        D2["Spark SQL 作业2<br/>分组聚合 ADS"]
        D3["Spark 作业3<br/>结果导出"]
    end

    subgraph L4["④ 应用服务层（Windows 主机）"]
        E1[("MySQL 8.0<br/>aq_ads 结果库")]
        F1["Spring Boot 2.7<br/>Controller / Service / Mapper"]
    end

    subgraph L5["⑤ 前端展示层（Windows 主机）"]
        G1["Vue3 大屏<br/>指标卡 + 4 图"]
        G2["数据管理页 / 查询页"]
    end

    subgraph L6["⑥ 独立分析层"]
        H1["Python + Matplotlib<br/>6 类静态图"]
    end

    A1 -->|"上传 hdfs dfs -put"| B1
    B1 -->|"读原始"| D1
    D1 -->|"写明细"| B2
    B2 --- C1
    B2 -->|"读明细"| D2
    D2 -->|"写结果"| B3
    B3 --- C1
    B3 -->|"读 ADS"| D3
    D3 -->|"JDBC 写入"| E1
    B3 -->|"导出 CSV/Parquet"| H1
    E1 -->|"MyBatis 查询"| F1
    F1 -->|"REST + JSON"| G1
    F1 -->|"REST + JSON"| G2
    H1 -->|"PNG + 底表 CSV"| I1["论文 / 答辩材料"]

    C1 -.->|"可选：JDBC 直连<br/>见第 4.3 节"| F1
~~~

**读图要点**：

- 实线是 V1 必做主链路；虚线是可选增强。
- 数据"单向流动"：CSV → ODS → DWD → ADS → MySQL → 接口 → 页面。任何一层都不回写上一层。
- Hive 不参与"搬运"，它负责**定义表结构**和**提供 SQL 查询入口**；真正的文件读写由 Spark 完成。

---

## 3. 数据流向（逐步说明）

| 步骤 | 动作 | 技术 | 产物 | 可验证点 |
| --- | --- | --- | --- | --- |
| S1 | 下载 12 个站点 CSV，记录文件大小与校验和 | 浏览器/scp | 本地 data/raw | 文件数 = 12，总大小与官网一致 |
| S2 | 上传到 HDFS 原始层，设为只读 | hdfs dfs -put / -chmod | /aq/ods/air_quality/ | hdfs dfs -ls 与本地一致 |
| S3 | 建 Hive 外部表映射原始 CSV | Hive DDL | ods_air_raw | select count(1) 与行数一致 |
| S4 | Spark SQL 读取原始表，执行 DQ-01~DQ-12 清洗 | PySpark | 明细 Parquet（按年/月分区） | 输出行数 = 清洗报告保留数 |
| S5 | 建 Hive 明细外部表 | Hive DDL | dwd_air_hourly | Hive count 与 Spark count 相等 |
| S6 | Spark SQL 聚合出 4 类 ADS 表 | PySpark | station_summary / monthly_trend / hourly_pattern / data_quality | 每表无重复主键 |
| S7 | 建 Hive ADS 外部表并抽查 | Hive DDL | ads_* | Hive 查询结果 = Spark 写出结果 |
| S8 | Spark 通过 JDBC 把 4 张 ADS 表写入 MySQL | PySpark + mysql-connector | aq_ads 库 | 行数与 Hive 一致 |
| S9 | Spring Boot 通过 MyBatis 查 MySQL，暴露 REST 接口 | Spring Boot | /api/v1/** | 接口返回值与 SQL 结果一致 |
| S10 | Vue3 调接口渲染大屏与查询页 | Vue3 + ECharts | 页面 | 页面数字 = 接口 = 数据库 |
| S11 | Matplotlib 读 ADS 导出文件出图 | Python | PNG + CSV | 与 S6 结果逐点一致 |

**为什么 S8 单独一步？** 因为它就是"大数据世界"到"应用世界"的交接点。Spark 有 JDBC 写能力，一行 df.write.jdbc 即可把结果落到 MySQL，比在 Spring Boot 里连 Hive 稳得多（理由见第 4 节）。

---

## 4. 关键设计决策：Spark 结果怎么交给 Spring Boot

### 4.1 三种候选方案

| 方案 | 做法 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **A. Hive JDBC 直连** | Spring Boot 引 hive-jdbc，直连 HiveServer2 查 ADS 表 | 无需额外库；数据"实时"；最能体现大数据与后端的直接连接 | 依赖虚拟机常开；HiveServer2 首查慢（数秒）；连接池不友好；JDBC 驱动与 Spring Boot 的 guava/jackson 版本易冲突 |
| **B. Spark 导出到 MySQL（选用）** | Spark 把 ADS 结果 JDBC 写入 MySQL，后端只查 MySQL | 稳定、快（毫秒级）、断网可用；MyBatis 生态成熟；前后端解耦 | 多一个 MySQL；数据有"同步延迟"（本项目为离线批处理，无影响） |
| **C. 结果文件直读** | Spark 导出 CSV/Parquet，后端启动时加载进内存 | 最简单，零外部依赖 | 无法分页查询、无并发控制；数据更新要重启；不像"系统" |

### 4.2 决策矩阵

| 评价维度（权重） | A 方案 | B 方案 | C 方案 |
| --- | --- | --- | --- |
| 演示可靠性（30%） | 2 | 5 | 4 |
| 查询性能（20%） | 2 | 5 | 4 |
| 开发难度（对初学者，20%） | 2 | 4 | 5 |
| 课程技术覆盖（20%） | 5 | 4 | 2 |
| 可扩展性（10%） | 3 | 4 | 1 |
| **加权得分** | **2.6** | **4.5** | **3.6** |

**结论**：主链路用 B；A 作为"可选增强"保留（用于明细/自定义查询演示，并在文档中论证可行性）；C 只作为开发早期的过渡手段，最终版本必须移除。

### 4.3 Hive JDBC 可行性分析（按要求单独研究）

**结论：技术上可行，但不宜作为大屏主通道。**

可行条件：

1. 虚拟机内启动 HiveServer2（默认端口 10000），metastore 服务（9083）同时可用。
2. Spring Boot 引入 hive-jdbc 3.1.x 与 hadoop-common 3.3.x，并排除冲突的 guava、jackson、slf4j 版本。
3. 连接串形如：jdbc:hive2://192.168.x.x:10000/default;auth=noSasl（具体认证方式以实际 hive-site.xml 为准）。
4. 虚拟机的 10000 端口对主机可达（NAT 端口映射或主机模式网络）。

已知风险：

| 风险 | 表现 | 应对 |
| --- | --- | --- |
| 驱动依赖冲突 | 启动报 NoSuchMethodError / NoClassDefFoundError（常见于 guava） | 用 dependencyManagement 锁定版本，必要时用 shade 打包 |
| 首次查询慢 | 3–10 秒，超时 | 连接超时设 10s 以上，接口加缓存 |
| 连接池不兼容 | HikariCP 校验连接失败 | 用简单连接池或每次新建连接（低频场景可接受） |
| 服务未启动 | 页面直接报错 | 接口降级到 MySQL 数据，返回提示"明细查询暂不可用" |
| Java 版本 | JDK 21 下反射告警 | 后端统一用 JDK 8（本项目已如此选择） |

因此 A 方案的定位是：**"明细/自定义查询"的可选通道，且必须实现失败降级**；不作为大屏聚合查询的主通道。

### 4.4 关于 Spark 与 Hive 的版本耦合（容易踩的坑）

Spark 3.5.x 自带的 Hive 客户端是 2.3.9，而 Hive 服务端若是 3.1.3，两者 metastore 协议版本不一致，直接让 Spark 读写 Hive 托管表可能报 schema 版本错误。

本项目的规避办法（也是选用"外部表"的原因）：

1. Spark **只负责写 Parquet 文件到 HDFS**，不写 Hive 托管表；
2. Hive 用 CREATE EXTERNAL TABLE ... STORED AS PARQUET LOCATION 的形式映射这些目录；
3. 这样 Hive 只读元数据，Spark 只写文件，**双方通过文件格式约定，而不是 metastore 协议耦合**。

如果后续确实需要 Spark 直接读 Hive 表，再配置：

~~~
spark.sql.hive.metastore.version=3.1.2
spark.sql.hive.metastore.jars=maven
~~~

（该配置需要联网下载 metastore 相关 jar，属于阶段三的进阶项，V1 不强制。）

---

## 5. 分层职责

| 层 | 部署位置 | 职责 | 明确不做 |
| --- | --- | --- | --- |
| 数据来源层 | 本地磁盘 | 保管官方原始文件与校验信息 | 不做任何修改 |
| 存储层 | 虚拟机 HDFS/Hive | 分层存放、表结构定义、SQL 查询 | 不做计算 |
| 计算层 | 虚拟机 Spark | 清洗、聚合、导出 | 不做展示 |
| 服务层 | Windows Spring Boot | 参数校验、业务口径、查询编排、导出 | 不做大数据计算 |
| 展示层 | 浏览器 Vue3 | 渲染、交互、联动 | 不做统计（只做格式化） |
| 分析层 | Windows Python | 静态图、交叉核对 | 不参与线上接口 |

**一条铁律**：统计口径只在 Spark SQL 里定义一次，后端与前端只做"取数 + 展示"，不得在 Java 或 JavaScript 里重新算均值。否则到处都是算法，答辩一问就露馅。

---

## 6. Maven 父子工程与后端三层架构

### 6.1 工程总体目录

~~~
D:\官方工作区\                       ← 项目根目录（当前工作区）
├── docs\                            ← 六份设计与审计文档
├── backend\                         ← Maven 父工程
│   ├── pom.xml                      ← packaging=pom，统一版本管理
│   ├── aqp-common\                  ← 公共模块（jar）
│   └── aqp-server\                  ← 服务模块（Spring Boot 可执行 jar）
├── frontend\                        ← Vue3 工程（npm 独立构建）
├── bigdata\                         ← PySpark 作业、Hive DDL、提交脚本
│   ├── jobs\
│   ├── ddl\
│   ├── conf\
│   └── logs\
├── analysis\                        ← Matplotlib 脚本与输出
│   ├── scripts\
│   └── output\
├── data\                            ← 原始数据（不入 Git）
│   ├── raw\
│   └── interim\
└── README.md
~~~

### 6.2 为什么后端只有两个 Maven 模块

| 模块 | 职责 | 为什么单独成模块 |
| --- | --- | --- |
| aqp-common | 统一返回体 Result、分页对象、错误码、通用工具、常量、跨模块 DTO | 避免业务代码里到处重复写返回结构；后续若加定时任务模块可复用 |
| aqp-server | 启动类、Controller、Service、Mapper、Entity、配置、异常处理 | 应用主体 |

**为什么不建 aqp-bigdata 模块**：本项目的 Spark 作业用 PySpark 编写（本机已有 PySpark 3.5.3 环境），不需要 Java 编译；塞进 Maven 只会增加打包复杂度而不产生价值。任务书也明确允许"前端、后端、大数据代码不必用同一种构建工具管理"。

**什么时候才加模块**：如果后续决定用 Java/Scala 写 Spark 作业，再加 aqp-bigdata（jar，spark-core 设 provided），届时父工程只需加一行 module。

### 6.3 后端三层架构

~~~mermaid
flowchart LR
    U["浏览器"] -->|"HTTP GET/POST"| C["Controller<br/>参数接收与校验"]
    C --> S["Service（接口 + 实现）<br/>业务口径与编排"]
    S --> M["Mapper（MyBatis）<br/>SQL 与结果映射"]
    M --> DB[("MySQL<br/>aq_ads")]
    S -.->|"可选"| HJ["HiveJdbcDao<br/>HiveServer2"]
    C --> R["统一返回 Result"]
    EX["GlobalExceptionHandler"] --- C
~~~

| 层 | 包名 | 允许做的事 | 禁止做的事 |
| --- | --- | --- | --- |
| Controller | com.aqp.server.controller | 接参、校验、调 Service、返回 Result | 写 SQL、写业务计算 |
| Service | com.aqp.server.service | 组合多次查询、校验业务规则、组织 VO | 直接拼 HTTP 响应 |
| Mapper | com.aqp.server.mapper | 单表/多表查询、分页 | 写业务判断 |
| Entity | com.aqp.server.entity | 对应数据库表 | 暴露给前端 |
| DTO/VO | com.aqp.server.dto / vo | 入参对象 / 出参对象 | 混用同一对象 |
| Config | com.aqp.server.config | 数据源、跨域、拦截器、接口文档 | 业务逻辑 |

**DTO 与 VO 为什么要分开**：DTO 是"前端传进来的"，VO 是"给前端看的"。混用会导致数据库字段直接暴露给页面，改表就崩页面。

### 6.4 接口约定

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/meta/dataset | 数据集元信息（记录数、站点数、时间范围、字段列表） |
| GET | /api/v1/quality/overview | 清洗前后记录数、缺失率、异常统计 |
| GET | /api/v1/quality/station | 各站点数据质量 |
| GET | /api/v1/stats/station | 站点对比（参数：pollutant、start、end） |
| GET | /api/v1/stats/monthly | 月度趋势 |
| GET | /api/v1/stats/hourly | 小时分布 |
| GET | /api/v1/records | 明细分页（station、start、end、page、size） |
| GET | /api/v1/records/export | 导出 CSV（同上参数，带行数上限） |

统一返回结构：

~~~
{ "code": 0, "message": "ok", "data": { ... }, "timestamp": 1690000000000 }
~~~

### 6.5 前端工程结构

~~~
frontend\
├── package.json
├── vite.config.js            ← 代理 /api 到 localhost:8080
├── index.html
└── src\
    ├── main.js
    ├── App.vue
    ├── router\index.js
    ├── api\                  ← 一个接口一个函数，统一 axios 实例
    ├── views\
    │   ├── Dashboard.vue     ← 可视化大屏
    │   ├── DataManage.vue    ← 数据管理与质量
    │   └── Query.vue         ← 明细查询与导出
    ├── components\
    │   ├── BaseChart.vue     ← ECharts 通用封装
    │   ├── FilterBar.vue     ← 站点/日期/污染物筛选
    │   └── StatCard.vue
    └── assets\
~~~

**前端只做三件事**：取数、格式化、画图。所有聚合都在 SQL 里完成。

### 6.6 大数据与 Python 目录职责

| 目录 | 内容 | 命名规则 |
| --- | --- | --- |
| bigdata/jobs | 01_clean.py、02_aggregate.py、03_export_mysql.py | 数字前缀表示执行顺序 |
| bigdata/ddl | 01_hive_ods.sql、02_hive_dwd.sql、03_hive_ads.sql | 与作业编号对应 |
| bigdata/conf | spark-defaults.conf、etl.yaml（路径与参数） | 参数外置，不写死在代码里 |
| analysis/scripts | fig01_station_compare.py 等 | 一图一脚本 |
| analysis/output | PNG + 底表 CSV | 文件名带生成日期 |

---

## 7. 部署拓扑与端口

| 组件 | 位置 | 端口 | 备注 |
| --- | --- | --- | --- |
| HDFS NameNode | 虚拟机 | 9870（Web）/ 8020（RPC） | 单机伪分布式 |
| YARN ResourceManager | 虚拟机 | 8088 | 若使用 local 模式可不启 |
| Hive Metastore | 虚拟机 | 9083 | |
| HiveServer2 | 虚拟机 | 10000 | 可选通道 |
| Spark Master UI | 虚拟机 | 8080 → **改为 8081** | 与 Spring Boot 撞端口，必须改 |
| MySQL | Windows | 3306 | 已安装 |
| Spring Boot | Windows | 8080 | |
| Vue 开发服务器 | Windows | 5173 | 生产打包后由 Nginx 或静态托管 |

**网络**：虚拟机用 NAT，主机访问虚拟机需固定 IP 或端口映射。阶段三确定最终方案并写入运行说明。

---

## 8. 配置、数据、日志、文档的存放位置

| 类别 | 位置 | 是否入 Git |
| --- | --- | --- |
| 源代码 | backend/、frontend/src、bigdata/jobs、analysis/scripts | 是 |
| 配置模板 | backend/*/src/main/resources/application.yml、bigdata/conf | 是（密码用占位符） |
| 本地真实配置 | 同目录 application-local.yml | 否（.gitignore） |
| 原始数据 | data/raw、HDFS /aq/ods | 否（体积大，只留校验和清单） |
| 中间结果 | data/interim、HDFS /aq/dwd | 否 |
| 分析图 | analysis/output | 是（PNG 体积小，作为成果留存） |
| 日志 | backend/logs、bigdata/logs | 否 |
| 文档 | docs/ | 是 |

---

## 9. 与课程"父子项目—大屏案例"的借鉴关系

借鉴的是**组织方式**：

1. 父工程统管版本，子模块各司其职；
2. 大屏按"指标卡—主图—辅图"的信息层级组织；
3. 前后端通过统一返回体对接；
4. 文档先行、按阶段推进。

**不借鉴**的是业务主题、页面文案、字段设计、图表组合与任何具体代码。本项目的数据、指标、页面结构均由北京市空气质量数据决定。

---

## 10. 架构风险与演进方向

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 虚拟机性能不足 | Spark 作业慢 | 单机 local 模式；4 核 8G 已分配；数据仅 40MB |
| 版本不匹配 | 作业报错 | 阶段二先核实 HDFS/Hive/Spark 版本，再定 DDL |
| 端口冲突 | 服务起不来 | 统一端口表，Spark UI 改 8081 |
| 演示时虚拟机未开 | 大屏无数据 | 采用 B 方案，页面读 MySQL 已有结果 |
| 数据同步遗漏 | 页面数字旧 | 导出作业幂等 + 每次记录同步时间并在页面显示"数据更新时间" |

演进方向（论文"展望"可用）：引入调度（Azkaban/DolphinScheduler）、把 MySQL 换成 ClickHouse 提升聚合性能、增加 Hive JDBC 实时明细通道、扩展为多城市对比（需另找数据源，不能编造）。
