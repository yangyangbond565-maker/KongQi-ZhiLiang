# 前端（Vue3 + Vite）

## 启动

先启动后端（8080），再：

    cd frontend
    npm install --cache "D:\\官方工作区\\.npm-cache"
    npm run dev

浏览器打开 http://localhost:5173/

开发服务器已配置代理：/api 转发到 http://127.0.0.1:8080，前端不需要改接口地址。

## 页面

- /#/          数据大屏：指标卡 + 站点柱状图 + 月度折线 + 24 小时折线，可切换污染物
- /#/query     统计查询：站点 / 月度 / 小时三张表，带分页

## 依赖

vue 3.5、vue-router 4、echarts 5.5、axios 1.7，构建用 vite 5。

## 说明

- 所有数据来自后端 /api 接口，没有写死的演示数字。
- 污染物选项与后端白名单一致：PM2.5、PM10、SO2、NO2、CO、O3。
- 浓度单位统一为 μg/m³（以 UCI 官方数据字典为准，CO 同为 μg/m³）。
- 若 npm 安装报 EPERM，多是缓存目录或子进程权限问题，可指定工作区内的 cache 目录。
