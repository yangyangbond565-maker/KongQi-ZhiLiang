# 项目启动与演示检查清单

> 城市空气质量大数据分析与可视化系统
> 用途：电脑重启后快速恢复演示环境。日常演示**不需要**启动 CentOS 虚拟机。

---

## 一、前置条件（已核实）

| 项 | 当前状态 | 说明 |
| --- | --- | --- |
| MySQL80 服务 | 运行中，启动类型为自动 | 开机自启，无需手动操作 |
| backend\.env.local | 存在（113 字节，含 AQ_DB_PASSWORD） | 不入库；换机需重新创建 |
| 后端 jar | aqp-server-1.0.0.jar 存在 | 若删除了 target 目录需重新打包 |
| 前端依赖 | frontend\node_modules 已安装 | 换机需执行 npm install |
| 端口 8080 / 5173 | 当前被现有进程占用（服务在运行） | 重启电脑后会释放 |

## 二、电脑重启后的启动顺序

### 第 1 步：确认 MySQL

正常情况下服务会自动启动。检查方式：

~~~powershell
Get-Service MySQL80
~~~

状态应为 Running。若为 Stopped，用管理员 PowerShell 执行：

~~~powershell
net start MySQL80
~~~

### 第 2 步：启动后端

~~~powershell
cd D:\官方工作区\backend
powershell -ExecutionPolicy Bypass -File .\run-backend.ps1
~~~

脚本会读取 .env.local 设置口令，然后运行 jar。看到下面这行即成功：

~~~
Started AqpServerApplication in ... seconds
~~~

若提示"未找到 jar"，先执行一次：

~~~powershell
cd D:\官方工作区\backend
mvn -DskipTests package
~~~

### 第 3 步：启动前端

~~~powershell
cd D:\官方工作区\frontend
npm run dev
~~~

看到 VITE ready 后访问：**http://localhost:5173/**

### 第 4 步：打开页面

| 地址 | 页面 |
| --- | --- |
| http://localhost:5173/#/ | 数据大屏（指标卡 + 3 张图） |
| http://localhost:5173/#/query | 统计查询（三张表 + 分页） |

## 三、演示前 30 秒自检

| 检查 | 期望 |
| --- | --- |
| 大屏指标卡 | 12 个站点、6 种污染物、412,029 条 PM2.5 样本、2013-03 ~ 2017-02 |
| 站点柱状图 | 12 根柱子，PM2.5 约 65–86 μg/m³ |
| 切换到 SO2 | 图表标题变化，柱子在 11–18 μg/m³ 区间 |
| 查询页 | 站点 12 条 / 月度 48 条 / 小时 24 条 |
| 浏览器控制台 | 无红色报错 |

## 四、关于 CentOS 虚拟机

- **日常演示不需要开机**：页面数据来自 MySQL 中已算好的统计结果，后端和前端都不依赖虚拟机。
- **只有重新计算数据时才需要开机**：虚拟机承载 HDFS、Hive、Spark SQL。
- 虚拟机路径：D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx
- 开机后确认：jps 能看到 NameNode、DataNode、ResourceManager、NodeManager、RunJar。

## 五、数据重算流程（需要虚拟机时）

重算不是全自动的，需要手动把结果传回 Windows。

~~~powershell
# 1) 启动虚拟机并取 IP
& 'D:\VMware\vmrun.exe' -T ws start 'D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx' nogui
& 'D:\VMware\vmrun.exe' -T ws getGuestIPAddress 'D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx' -wait

# 2) 传脚本到虚拟机
scp -i D:\BigDataLab\ssh\hadoop_vm_rsa bigdata\ddl\04_spark_ads.sql root@<IP>:/tmp/
scp -i D:\BigDataLab\ssh\hadoop_vm_rsa bigdata\run_ads_pipeline.sh root@<IP>:/tmp/
~~~

~~~bash
# 3) 虚拟机内执行：Spark SQL 计算 + 合并 CSV
bash /tmp/run_ads_pipeline.sh /tmp/04_spark_ads.sql
# 预期 73 / 289 / 145 行（含表头）
~~~

~~~powershell
# 4) 拷回三个 CSV
foreach ($n in 'station_pollutant','monthly_trend','hourly_pattern') {
  scp -i D:\BigDataLab\ssh\hadoop_vm_rsa "root@<IP>:/tmp/ads_$n.csv" "D:\官方工作区\data\interim\ads\ads_$n.csv"
}

# 5) 生成导入脚本并执行（DROP 仅限 aq_air 的三张 ADS 表）
cd D:\官方工作区
python scripts\load_ads_to_mysql.py
Get-Content .\data\interim\load_ads.sql -Encoding UTF8 | & 'D:\MYSQL\bin\mysql.exe' -u root -p --default-character-set=utf8mb4
~~~

重算后刷新页面即可看到新数据，后端不用重启（数据是实时查库的）。

## 六、停止服务

| 服务 | 方法 |
| --- | --- |
| 后端 | 在其窗口按 Ctrl+C，或结束对应 java 进程 |
| 前端 | 在其窗口按 Ctrl+C，或结束对应 node 进程 |
| 虚拟机 | & 'D:\VMware\vmrun.exe' -T ws stop 'D:\BigDataLab\Hadoop-CentOS7\Hadoop-CentOS7.vmx' soft |

## 七、常见问题

| 现象 | 处理 |
| --- | --- |
| 后端启动报数据源错误 | 确认 MySQL80 在运行、.env.local 存在 |
| 页面提示无法连接后端 | 8080 未监听，检查后端窗口是否还开着 |
| 页面能开但图表空白 | 查询 MySQL 三张表是否有数据 |
| 8080 被占用 | 换端口或结束占用进程 |
| npm run dev 报错 | 确认 node_modules 存在，否则 npm install |

## 八、当前已知状态（不影响演示）

| 事项 | 状态 | 是否影响演示 |
| --- | --- | --- |
| PySpark | 未使用。虚拟机只有 Python 2.7，统计改由 spark-sql 完成 | 不影响，结果已入库 |
| 自动化测试 | 没有。验收靠手工核对接口与页面 | 不影响，核对记录在 docs 中 |
| ECharts 打包体积 | 全量引入，构建提示超过 500 kB | 不影响，仅构建警告 |
| 数据重算 | 手工传文件 + 手工导入 | 不影响日常演示 |
