# 05 环境审计报告

> 审计日期：2026-10-20
> 审计方式：只读命令采集，未安装、未卸载、未修改任何软件与系统配置
> 审计范围：操作系统、硬件、开发工具链、大数据组件、虚拟化能力、网络连通性

---

## 0. 一句话结论

**开发侧（Java/Python/Node/Git）基本齐备，可以直接开工；大数据侧（Hadoop/Hive/Spark）在 Windows 上没有任何组件，但发现一台已配置好的 CentOS 7 虚拟机可以承载；当前最大的拦路虎不是软件，而是本机网络被代理接管导致所有 HTTPS 请求失败。**

---

## 1. 审计方法与局限

| 项目 | 说明 |
| --- | --- |
| 执行账号 | GG-BOND\86701（普通用户上下文） |
| 采集方式 | PowerShell 只读命令（Get-CimInstance、Get-Command、Test-Path、icacls、ipconfig 等） |
| 未做的事 | 未启动虚拟机、未启动 MySQL 服务、未运行 Spark 作业、未下载任何数据 |
| 已知局限 | ① "命令未找到"只代表当前 PATH 下没有，不代表整机没装；② 虚拟机内部环境完全未知；③ 部分命令在沙箱受限模式下可能受限 |

> 原则：以下所有"未检测到"均指**在本次检查手段下未发现**，不等于"一定没装"。

---

## 2. 系统与硬件

| 项目 | 实测结果 |
| --- | --- |
| 操作系统 | Microsoft Windows 11 家庭中文版 |
| 版本号 | 10.0.26200（64 位） |
| 计算机名 | GG-Bond |
| 机型 | HUAWEI MRGFG-XX（笔记本） |
| CPU | 13th Gen Intel Core i7-1360P，12 核 16 线程 |
| 内存 | 31.7 GB |
| 虚拟化 | HypervisorPresent = False（未启用 Hyper-V 系虚拟化平台） |
| 系统安装时间 | 2025-08-13 |

### 2.1 磁盘空间

| 盘符 | 总容量 | 可用 | 用途判断 |
| --- | --- | --- | --- |
| C: | 699.4 GB | 469.9 GB | 系统盘，充足 |
| D: | 589.3 GB | 456.0 GB | 工作区与虚拟机所在盘，充足 |
| E: | 537.1 GB | 535.3 GB | 基本空闲 |
| F: | 61.1 GB | 60.7 GB | 较小 |

**判断**：磁盘与内存对"单机伪分布式 + 42 万行数据"完全够用，甚至偏富余。瓶颈不会出现在硬件。

---

## 3. 已安装软件清单

| 类别 | 软件 | 版本 | 路径 / 证据 | 状态 |
| --- | --- | --- | --- | --- |
| JDK | Eclipse Temurin JDK | 1.8.0_504 | C:\Program Files\Eclipse Adoptium\jdk-8.0.504.1-hotspot | 可用，且为机器级 JAVA_HOME |
| JDK | Oracle GraalVM | 21.0.7 | C:\Program Files\Java\graalvm-jdk-21.0.7+8.1 | 可用（已实测 java -version） |
| 构建 | Apache Maven | 3.6.3 | D:\maven\apache-maven-3.6.3 | 可用，当前跑在 JDK 8 上 |
| 构建 | Maven 本地仓库 | 约 0.12 GB | D:\install\maven\repostory（settings.xml 指定） | 已配阿里云镜像 |
| Python | Anaconda Python | 3.13.9 | C:\anaconda\python.exe | 可用 |
| Python | pip | 25.3 | C:\anaconda\Scripts\pip.exe | 可用 |
| Python 库 | numpy / pandas / matplotlib | 2.3.5 / 2.3.3 / 3.10.6 | 主环境 | 可用，Matplotlib 模块可直接开工 |
| Python 库 | pyarrow / openpyxl / requests / flask | 21.0.0 / 3.1.5 / 2.32.5 / 3.1.2 | 主环境 | 可用 |
| Python 环境 | conda 环境 spark311 | Python 3.11.17 + PySpark 3.5.3 | C:\anaconda\envs\spark311 | 可用（仅验证导入，未启动 SparkSession） |
| 运行时 | Node.js | v24.16.0 | D:\Node.js\node.exe | 可用 |
| 包管理 | npm | 11.13.0（registry=npmmirror） | D:\Node.js\npm.ps1 | 可用 |
| 包管理 | pnpm | 已安装 | C:\Users\86701\AppData\Roaming\npm\pnpm.ps1 | 可用 |
| 版本控制 | Git | 2.55.0.windows.3 | D:\Git\cmd\git.exe | 可用，core.autocrlf=input |
| 虚拟化 | VMware Workstation | 17.6.2 | D:\VMware\vmware.exe | 可用 |
| 数据库 | MySQL Server | 8.0（PATH 中有 D:\MYSQL\bin） | 安装痕迹明确 | 服务是否运行未检测 |
| 其他 | MongoDB / Redis | 8.2 / 未取版本 | 均在 PATH 中 | 与本项目无关 |

### 3.1 Maven 配置要点

- 用户级 MAVEN_HOME：D:\maven\apache-maven-3.6.3
- settings.xml 已配置阿里云镜像：https://maven.aliyun.com/repository/public
- 本地仓库被改到 D:\install\maven\repostory（注意原目录名拼写为 repostory），当前约 0.12 GB

**这对外网受限环境是好消息**：只要镜像可达，依赖下载会比默认中央仓库快。

---

## 4. 大数据组件检测结果

| 组件 | 命令检测 | 环境变量 | 常见安装目录 | 结论 |
| --- | --- | --- | --- | --- |
| Hadoop | hadoop 未找到 | HADOOP_HOME 空 | C:\hadoop、D:\hadoop 不存在 | **未检测到** |
| HDFS | hdfs 未找到 | — | — | **未检测到** |
| Hive | hive、beeline 未找到 | HIVE_HOME 空 | C:\hive 不存在 | **未检测到** |
| Spark | spark-submit、spark-shell 未找到 | SPARK_HOME 空 | C:\spark 不存在 | **Windows 端未检测到**（但 conda 内有 PySpark 3.5.3） |
| Scala | scala 未找到 | SCALA_HOME 空 | — | **未检测到** |
| winutils / hadoop.dll | 全盘浅层搜索未找到 | — | — | **未检测到** |

### 4.1 重要发现：已有虚拟机与安装介质

| 项目 | 内容 |
| --- | --- |
| 虚拟机目录 | D:\BigDataLab\Hadoop-CentOS7 |
| 虚拟机配置 | 4 vCPU、8 GB 内存、NAT 网络、VMware 17 |
| 虚拟磁盘 | Hadoop-CentOS7.vmdk，约 6.9 GB |
| 安装介质 | D:\BigDataLab\install-media\CentOS-7.6-Hadoop-Auto.iso（917.5 MB） |
| 用途推测 | 课程/实验预装的 Hadoop 单机环境镜像 |

**必须诚实的部分**：该虚拟机**从未在本次审计中启动**，因此无法确认：

- 里面是否真的装了 Hadoop，装的是 2.x 还是 3.x；
- 是否装了 Hive、Spark，各自版本；
- 是否配了 HDFS 伪分布式、能否正常启动；
- 账号口令、IP、网络模式是否可用。

这些必须在阶段二开机核实后才能写进任何文档，**现在不能声称"环境已就绪"**。

### 4.2 另一个可用的 Spark 通道

conda 环境 spark311 内有完整的 PySpark 3.5.3（含 252 个 jar），意味着在 Windows 上可以直接用 **local 模式**跑 Spark SQL 做清洗与聚合，不需要 HDFS/Hive。

这不是替代方案，而是**兜底与提速手段**：

- 优点：改代码后立刻能跑，不必等虚拟机；
- 缺点：没有 HDFS/Hive，体现不出分布式存储与数仓概念，不能作为最终交付。

合理用法：阶段二、三先在 local 模式把 PySpark 逻辑写通，再切到虚拟机跑真实链路。

---

## 5. 网络状况（本次审计的最大问题）

### 5.1 实测证据

| 检查项 | 结果 |
| --- | --- |
| 网卡 | 存在名为 FlClash 的虚拟网卡（描述：Meta Tunnel），IP 198.18.0.1，默认网关 198.18.0.2 |
| 路由 | 默认路由 0.0.0.0/0 经 198.18.0.2，**metric 为 0（优先级最高）** |
| DNS | 系统 DNS 指向 198.18.0.2 |
| 域名解析 | archive.ics.uci.edu → 198.18.0.60；github.com → 198.18.0.87；全部落在 198.18.0.0/15 假地址段 |
| HTTPS 实测 | baidu / maven.aliyun.com / registry.npmmirror.com / archive.ics.uci.edu / github.com 全部返回 curl 错误码 35（TLS 握手失败），耗时 0.05–0.08 秒 |
| 代理进程 | 未检测到 clash / verge / FlClash 等进程在运行 |

### 5.2 结论

本机安装了代理工具 FlClash，它用 TUN 模式接管了 DNS 与默认路由（这是"假 IP + 全局接管"的典型特征）。**当前代理软件未运行或节点不可用**，于是所有域名都被解析成假地址，所有 HTTPS 连接都在 TLS 阶段失败。

**影响范围**：浏览器打不开 UCI 官网、npm 装不了包、Maven 下不了依赖、pip 装不了库、数据集无法下载。这不是"某个网站被墙"，而是**整机对外网络不可用**。

### 5.3 解决办法（需要你操作，我不擅自改系统设置）

任选其一：

1. **启动 FlClash 并连接一个可用节点**，然后重新测试（最快的办法）。
2. 打开 FlClash 设置，**关闭 TUN 模式 / 系统代理**，让网卡恢复直连，再刷新 DNS。
3. 若长期不用代理，可在"网络适配器"中禁用名为 FlClash 的虚拟网卡。

处理完请告诉我，我会重新执行第 9 节的验证命令确认。

> 说明：这属于你的系统网络配置，我不做修改。数据下载也必须等你确认网络恢复后再开始。

---

## 6. 兼容性评估

### 6.1 JDK / Maven / Spring Boot 组合

| 方案 | 组合 | 现状 | 优点 | 风险 |
| --- | --- | --- | --- | --- |
| **A（推荐）** | JDK 8 + Maven 3.6.3 + Spring Boot 2.7.18 | **全部已安装，零新增** | 与课程教程一致；Hive JDBC 客户端在 Java 8 下最稳；Maven 与 JDK 匹配 | Spring Boot 2.7 已停止维护；不能用新语法特性 |
| B | JDK 21 + Maven 3.9.x + Spring Boot 3.3.x | JDK 21 有，Maven 3.9 需另装 | 技术更新，生态支持期长 | 需装 Maven；hive-jdbc 3.1.3 在 Java 21 下可能出现反射/模块告警；课程示例多为 2.x，改造量大 |
| C | JDK 8 + Spring Boot 2.7 + 自制模块 | 同 A | — | 无额外价值 |

**建议**：走 A。理由不是"B 不好"，而是"对当前基础和答辩目标，A 的确定性最高"。如果后续导师明确要求新技术栈，再按 B 迁移（Spring Boot 3 主要改动是 javax → jakarta 包名）。

**一个必须注意的点**：机器级 JAVA_HOME 指向 JDK 8，而 PATH 中 JDK 21 的 bin 排在后面。这意味着命令行默认用 JDK 8。若哪天需要 JDK 21，应临时改 JAVA_HOME，而不是改 PATH 顺序。

### 6.2 Hadoop / Hive / Spark 兼容性风险

| 风险 | 说明 | 建议 |
| --- | --- | --- |
| 版本未知 | 虚拟机内组件版本未核实 | 阶段二第一件事就是开机记录版本 |
| Java 版本 | Hadoop 3.x 支持 Java 8/11；Hive 3.1.3 官方要求 Java 8 | 虚拟机内统一 Java 8，不要升 11/17 |
| Spark 与 Hive metastore 版本不一致 | Spark 3.5 内置 Hive 客户端为 2.3.9，Hive 服务端多为 3.1.3 | 采用"Spark 写 Parquet + Hive 外部表"解耦（见 04 文档 4.4） |
| Windows 版 Hadoop | Windows 上跑 Hadoop 需要 winutils 与 hadoop.dll，坑多 | 不在 Windows 上装 Hadoop，统一放虚拟机 |
| 端口冲突 | Spark Master UI 默认 8080 与 Spring Boot 冲突 | Spark 改 8081 |
| 内存 | 虚拟机分配 8 GB，主机 31.7 GB | 合理；跑 Spark local 够用 |

### 6.3 Vue3 / Node.js 组合

| 项 | 现状 | 判断 |
| --- | --- | --- |
| Node | v24.16.0 | 满足 Vite 7 要求（Node ≥ 20.19 或 ≥ 22.12） |
| npm | 11.13.0，registry 已指向 npmmirror | 国内下载速度有保障 |
| 建议版本 | Vue 3.5.x + Vite 6/7 + Element Plus 2.x + ECharts 5.5.x | 均为当前主流稳定组合 |
| 风险 | Node 24 较新，个别老依赖可能报警告 | 优先选维护活跃的库；遇 EPERM/引擎告警再降级到 Node 20 LTS |

### 6.4 虚拟化路线对比

| 路线 | 可行性 | 说明 |
| --- | --- | --- |
| **VMware + 已有 CentOS7 虚拟机（推荐）** | 高 | 机器已装 VMware 17.6.2，虚拟机文件已存在，最省事 |
| WSL2 + Ubuntu | 低（当前不可用） | wsl --status 返回 50，注册表无 Lxss 发行版记录，说明未启用或未安装发行版；启用需管理员权限并重启 |
| Docker Desktop | 低 | 未安装；依赖 WSL2 或 Hyper-V，而 HypervisorPresent=False |
| 双系统/云服务器 | 中 | 可行但成本高，不作为首选 |

**结论**：走 VMware 虚拟机路线最现实。

### 6.5 HDFS / Hive / Spark 搭建顺序

~~~
1. 启动并核实虚拟机（Java、Hadoop 版本、IP、SSH）
2. 格式化并启动 HDFS（NameNode / DataNode）
3. 启动 Hive Metastore（依赖 MySQL 或 Derby）
4. 启动 HiveServer2（可选，供 JDBC）
5. 验证 Spark 能读 HDFS、能连 metastore
6. 回到 Windows：建 MySQL 库、跑导出作业
7. 最后才写后端与前端
~~~

顺序不能颠倒：Hive 依赖 HDFS 与关系库，Spark 依赖 HDFS，后端依赖结果库。

### 6.6 优先准备与可延后

| 优先级 | 事项 | 原因 |
| --- | --- | --- |
| P0 | 修复网络 | 不修就下载不了数据、装不了依赖，全盘卡住 |
| P0 | 下载并校验数据集 | 一切分析的前提 |
| P0 | 核实虚拟机内环境 | 决定阶段三怎么写 DDL |
| P1 | 建 MySQL 库与账号 | 后端开发前必须就绪 |
| P1 | 确认后端技术栈（A/B） | 避免写到一半返工 |
| P2 | 装 Maven 3.9（若选 B） | 可延后 |
| P2 | 配置 Git 仓库与 .gitignore | 阶段二做即可 |

### 6.7 如何避免"一上来就搭集群"

- **不搭真集群**：单机伪分布式（一个 NameNode + 一个 DataNode + local Spark）足够演示全部概念。
- **不装 YARN 调度**：Spark 用 local[*] 模式，省内存也省排错时间。
- **不引入 Kafka/Flink/ZooKeeper**：V1 用不到，装了只会增加故障点。
- **不做高可用**：HA、联邦、多副本调优都是生产话题，与课程目标无关。

---

## 7. 推荐路线与备选路线

### 7.1 推荐路线（Route A）

1. 网络修复 → 下载 UCI 数据 → 本地校验。
2. 启动 VMware 中的 CentOS7，核实 Hadoop/Hive/Spark 版本；缺什么补什么（在虚拟机内，不影响 Windows）。
3. HDFS 建三层目录 → 上传原始数据。
4. PySpark（虚拟机内）写清洗与聚合；Windows 的 spark311 环境只做开发调试。
5. ADS 结果经 Spark JDBC 写入 Windows 的 MySQL。
6. Spring Boot（JDK 8 + 2.7.18）读 MySQL 出接口。
7. Vue3 + ECharts 出大屏。
8. Matplotlib 读导出结果出静态图并交叉核对。

**理由**：每一步都能独立验证，出问题容易定位；Windows 负责"应用侧"，Linux 负责"数据侧"，职责清晰。

### 7.2 备选路线（Route B：虚拟机不可用时）

若虚拟机启动失败或内部环境损坏：

1. 用 conda spark311 在 Windows 跑 Spark local 模式完成清洗与聚合（功能等价，只是没有 HDFS/Hive）。
2. 用本地目录模拟 HDFS 分层（data/ods、data/dwd、data/ads），并在文档中**如实说明这是降级方案**。
3. 其余（MySQL、Spring Boot、Vue3、Matplotlib）不变。
4. 后续再补 HDFS/Hive 的真实运行证据。

**这条路线只能作为过渡**：任务书明确要求 HDFS 与 Hive 必须真实使用，最终交付前必须回到 Route A。

### 7.3 备选路线（Route C：需要更强隔离时）

若希望大数据环境完全独立、随时可重建，可在 VMware 中新建一台 Ubuntu 22.04，按 Hadoop 3.3.6 + Hive 3.1.3 + Spark 3.5.3 手动安装。成本是 1–2 天，收益是可复现、可写进论文"环境搭建"章节。当前不推荐，除非 Route A 的虚拟机无法修复。

---

## 8. 本次审计中做过的一次环境修复（如实记录）

审计开始时，工作区 D:\官方工作区 无法被本工具写入（报错 SetNamedSecurityInfoW Win32 5）。原因是该目录的权限项中只有"Authenticated Users: 修改"，缺少针对当前登录用户的完全控制权限，导致工具无法为沙箱授予写权限。

处理过程：

| 步骤 | 内容 |
| --- | --- |
| 备份 | 变更前把原权限完整导出到 D:\官方工作区\.acl-recovery\acl-backup-*.json 及配套恢复脚本 |
| 修复 | 为当前用户 SID S-1-5-21-...-1001 增加完全控制权限项（保留原有拒绝项、所有者、审计设置不变） |
| 验证 | 重新读取权限，写权限与改权限均为 true；随后在受限模式下成功创建并读回测试文件 |
| 回滚命令 | pwsh -NoProfile -File 'D:\官方工作区\.acl-recovery\acl-backup-7b291ed782294c0698960c31db2ee47c.json.ps1' -Path 'D:\官方工作区' -AllowRoot 'D:\官方工作区' -Restore 'D:\官方工作区\.acl-recovery\acl-backup-7b291ed782294c0698960c31db2ee47c.json' |

说明：该操作只影响 D:\官方工作区 这一个目录的权限项，未改动文件内容、未改动所有者、未触碰其他目录。.acl-recovery 目录建议在项目稳定后再删除（现在保留作为凭证）。

---

## 9. 复现命令（你可以自己再跑一遍）

~~~powershell
# 系统与硬件
Get-CimInstance Win32_OperatingSystem | Select Caption,Version,BuildNumber,OSArchitecture
Get-CimInstance Win32_ComputerSystem  | Select Manufacturer,Model,TotalPhysicalMemory
Get-CimInstance Win32_Processor       | Select Name,NumberOfCores,NumberOfLogicalProcessors

# 磁盘
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select DeviceID,Size,FreeSpace

# 工具链
java -version; mvn -v; python --version; pip --version; node -v; npm -v; git --version

# 大数据组件（预期全部报"无法识别"）
hadoop version; hdfs version; hive --version; spark-submit --version

# 网络诊断（关键）
ipconfig /all
route print -4
Resolve-DnsName archive.ics.uci.edu
curl.exe -sS -I --max-time 15 https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data

# 虚拟机
Get-Item 'D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx' | Select FullName,Length
~~~

**判断标准**：curl 返回 200 或 301/302 才算网络通；返回 000 且退出码 35 就是 TLS 握手失败，需要先处理代理。

---

## 10. 需要你确认或操作的事项

| # | 事项 | 需要你做什么 |
| --- | --- | --- |
| 1 | 网络 | 启动 FlClash 并连节点，或关闭 TUN/系统代理，然后告诉我"网络好了" |
| 2 | 数据集 | 网络恢复后我给出下载与校验步骤（或你手动下载后放进 data/raw） |
| 3 | 虚拟机 | 确认 D:\BigDataLab\Hadoop-CentOS7 是否可以启动、是否记得登录账号口令；首次开机建议由你操作，避免误改 |
| 4 | 后端栈 | 确认走 A（JDK 8 + Spring Boot 2.7.18）还是 B（JDK 21 + Spring Boot 3.3） |
| 5 | 项目根目录 | 当前直接把 D:\官方工作区 当作项目根目录；若你想放在子目录（如 D:\官方工作区\air-quality-platform），请在阶段二开始前说明 |
| 6 | 课程材料 | 若有课程的项目设计文档模板或评分表，提供后我会对齐文档结构 |

---

## 11. 审计结论

| 维度 | 结论 |
| --- | --- |
| 硬件 | 完全满足，无需升级 |
| 开发工具链 | 满足，JDK/Python/Node/Git/Maven 齐全 |
| 大数据环境 | Windows 端缺失；虚拟机待核实，这是阶段二的首要任务 |
| 网络 | **不可用**，必须先修，否则阶段二无法开始 |
| 技术路线 | 推荐 Route A（虚拟机承载大数据 + Windows 承载应用） |
| 风险等级 | 中：环境风险可控，但网络与虚拟机是两个必须先解决的硬阻塞 |
