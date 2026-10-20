# -*- coding: utf-8 -*-
"""
城市空气质量大数据分析与可视化系统 —— Matplotlib 独立分析图表

数据来源（全部为项目内真实数据，不使用任何演示数据）：
  1. data/interim/ads/ads_station_pollutant.csv   Spark SQL 站点统计结果
  2. data/interim/ads/ads_monthly_trend.csv       Spark SQL 月度统计结果
  3. data/interim/ads/ads_hourly_pattern.csv      Spark SQL 小时统计结果
  4. data/interim/quality_summary.json            Python 数据质量检查结果
  5. data/raw/prsa2017/stations/.../*.csv         原始 12 个站点 CSV（季节、相关性）

输出：
  analysis/output/*.png   六张分析图
  analysis/output/*.csv   每张图对应的底表，便于复核

运行：
  python analysis/matplotlib_charts.py
"""
import json
import os
import glob

import matplotlib
matplotlib.use("Agg")  # 无界面后端，方便脚本化运行
import matplotlib.pyplot as plt
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADS_DIR = os.path.join(BASE, "data", "interim", "ads")
RAW_DIR = os.path.join(BASE, "data", "raw", "prsa2017", "stations",
                       "PRSA_Data_20130301-20170228")
QUALITY_JSON = os.path.join(BASE, "data", "interim", "quality_summary.json")
OUT_DIR = os.path.join(BASE, "analysis", "output")

POLLUTANTS = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]
SEASON_ORDER = ["春", "夏", "秋", "冬"]


def setup_font():
    """中文字体：优先微软雅黑，其次黑体，最后宋体。"""
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120


def check_inputs():
    missing = []
    for name in ["ads_station_pollutant.csv", "ads_monthly_trend.csv", "ads_hourly_pattern.csv"]:
        if not os.path.exists(os.path.join(ADS_DIR, name)):
            missing.append(os.path.join(ADS_DIR, name))
    if not os.path.exists(QUALITY_JSON):
        missing.append(QUALITY_JSON)
    if not os.path.isdir(RAW_DIR):
        missing.append(RAW_DIR)
    if missing:
        raise SystemExit("缺少输入文件：\n" + "\n".join(missing))


def load_ads():
    station = pd.read_csv(os.path.join(ADS_DIR, "ads_station_pollutant.csv"))
    monthly = pd.read_csv(os.path.join(ADS_DIR, "ads_monthly_trend.csv"))
    hourly = pd.read_csv(os.path.join(ADS_DIR, "ads_hourly_pattern.csv"))
    return station, monthly, hourly


def load_raw():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not files:
        raise SystemExit("未找到原始 CSV：" + RAW_DIR)
    frames = [pd.read_csv(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def save(fig, name, data):
    os.makedirs(OUT_DIR, exist_ok=True)
    fig.tight_layout()
    png = os.path.join(OUT_DIR, name + ".png")
    csv = os.path.join(OUT_DIR, name + ".csv")
    fig.savefig(png, bbox_inches="tight")
    plt.close(fig)
    data.to_csv(csv, index=False, encoding="utf-8-sig")
    print("  已生成 %s.png / .csv" % name)


def fig_station(station):
    """图1：站点对比柱状图，回答“哪个站点 PM2.5 更高”。"""
    df = station[station["pollutant"] == "PM2.5"].sort_values("station")
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.bar(df["station"], df["avg_value"], color="#3b82f6", edgecolor="#1e3a8a")
    ax.set_title("各监测站点 PM2.5 平均浓度（2013-03 至 2017-02）", fontsize=13)
    ax.set_xlabel("监测站点")
    ax.set_ylabel("浓度（μg/m³）")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", fontsize=9)
    for x, y in zip(df["station"], df["avg_value"]):
        ax.text(x, y + 0.8, "%.1f" % y, ha="center", fontsize=8)
    save(fig, "fig1_station_compare", df)


def fig_monthly(monthly):
    """图2：月度趋势折线图，回答“浓度随月份怎么变化”。"""
    df = monthly[monthly["pollutant"] == "PM2.5"].copy()
    df["label"] = df["obs_year"].astype(str) + "-" + df["obs_month"].astype(str).str.zfill(2)
    df = df.sort_values(["obs_year", "obs_month"])
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(df["label"], df["avg_value"], color="#0ea5e9", linewidth=1.8, marker="o", markersize=3)
    ax.set_title("PM2.5 月度平均浓度趋势（48 个月）", fontsize=13)
    ax.set_xlabel("年-月")
    ax.set_ylabel("浓度（μg/m³）")
    ax.grid(linestyle="--", alpha=0.35)
    step = 4
    ax.set_xticks(range(0, len(df), step))
    ax.set_xticklabels(df["label"].iloc[::step], rotation=40, ha="right", fontsize=8)
    save(fig, "fig2_monthly_trend", df)


def fig_hourly(hourly):
    """图3：24 小时分布折线图，回答“一天中什么时候浓度高”。"""
    df = hourly[hourly["pollutant"] == "PM2.5"].sort_values("obs_hour")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["obs_hour"], df["avg_value"], color="#8b5cf6", linewidth=1.8, marker="o", markersize=4)
    ax.set_title("PM2.5 一天中不同小时的平均浓度", fontsize=13)
    ax.set_xlabel("小时（0–23 时）")
    ax.set_ylabel("浓度（μg/m³）")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(linestyle="--", alpha=0.35)
    save(fig, "fig3_hourly_pattern", df)


def fig_missing():
    """图4：缺失率柱状图，回答“哪些字段缺失严重”。"""
    with open(QUALITY_JSON, encoding="utf-8") as f:
        summary = json.load(f)
    rows = [m for m in summary["missing"] if m["ratio"] > 0]
    df = pd.DataFrame(rows).sort_values("ratio", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(df["field"], df["ratio"], color="#f97316")
    ax.set_title("各字段缺失率（共 420,768 条记录）", fontsize=13)
    ax.set_xlabel("缺失率（%）")
    ax.set_ylabel("字段")
    for y, v in zip(df["field"], df["ratio"]):
        ax.text(v + 0.03, y, "%.2f%%" % v, va="center", fontsize=8)
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    save(fig, "fig4_missing_rate", df)


def fig_season(raw):
    """图5：季节对比柱状图，回答“哪个季节污染更重”。"""
    season_map = {12: "冬", 1: "冬", 2: "冬", 3: "春", 4: "春", 5: "春",
                  6: "夏", 7: "夏", 8: "夏", 9: "秋", 10: "秋", 11: "秋"}
    tmp = pd.DataFrame({
        "season": raw["month"].map(season_map),
        "pm25": pd.to_numeric(raw["PM2.5"], errors="coerce"),
    })
    df = (tmp.dropna(subset=["pm25"])
            .groupby("season")["pm25"]
            .agg(avg_value="mean", valid_cnt="count")
            .reindex(SEASON_ORDER)
            .reset_index())
    df["avg_value"] = df["avg_value"].round(2)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(df["season"], df["avg_value"], color=["#22c55e", "#ef4444", "#eab308", "#3b82f6"])
    ax.set_title("不同季节 PM2.5 平均浓度（按原始小时数据统计）", fontsize=13)
    ax.set_xlabel("季节（3–5 春，6–8 夏，9–11 秋，12–2 冬）")
    ax.set_ylabel("浓度（μg/m³）")
    for x, y, c in zip(df["season"], df["avg_value"], df["valid_cnt"]):
        ax.text(x, y + 1, "%.2f\n(n=%s)" % (y, format(c, ",")), ha="center", fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    save(fig, "fig5_season_compare", df)


def fig_corr(raw):
    """图6：污染物相关性热力图，回答“污染物之间是否同涨同跌”。"""
    data = raw[POLLUTANTS].apply(pd.to_numeric, errors="coerce")
    corr = data.corr().round(3)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(corr.values, cmap="RdYlBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(POLLUTANTS)))
    ax.set_yticks(range(len(POLLUTANTS)))
    ax.set_xticklabels(POLLUTANTS)
    ax.set_yticklabels(POLLUTANTS)
    ax.set_title("六种污染物浓度的相关系数（Pearson）", fontsize=13)
    for i in range(len(POLLUTANTS)):
        for j in range(len(POLLUTANTS)):
            ax.text(j, i, "%.2f" % corr.values[i, j], ha="center", va="center",
                    fontsize=8, color="black")
    fig.colorbar(im, ax=ax, shrink=0.85, label="相关系数")
    out = corr.reset_index().rename(columns={"index": "pollutant"})
    save(fig, "fig6_pollutant_corr", out)


def verify(station, monthly, hourly, raw):
    """关键数值核对：与 Spark/MySQL/Python 已验证的结果比对。"""
    print("\n关键数值核对：")
    checks = []

    rows = len(raw)
    checks.append(("原始记录数", rows, 420768))

    s = station[(station["pollutant"] == "PM2.5")]
    checks.append(("站点数", s["station"].nunique(), 12))
    checks.append(("PM2.5 有效样本合计", int(s["valid_cnt"].sum()), 412029))

    m = monthly[(monthly["pollutant"] == "PM2.5") & (monthly["obs_year"] == 2013) & (monthly["obs_month"] == 3)]
    checks.append(("2013-03 PM2.5 均值", round(float(m["avg_value"].iloc[0]), 2), 104.89))
    checks.append(("2013-03 PM2.5 样本", int(m["valid_cnt"].iloc[0]), 8881))

    h = hourly[(hourly["pollutant"] == "PM2.5") & (hourly["obs_hour"] == 10)]
    checks.append(("10 时 PM2.5 均值", round(float(h["avg_value"].iloc[0]), 2), 77.12))
    checks.append(("10 时 PM2.5 样本", int(h["valid_cnt"].iloc[0]), 17162))

    so2 = station[(station["pollutant"] == "SO2") & (station["station"] == "Aotizhongxin")]
    checks.append(("Aotizhongxin SO2 均值", round(float(so2["avg_value"].iloc[0]), 2), 17.38))
    checks.append(("Aotizhongxin SO2 样本", int(so2["valid_cnt"].iloc[0]), 34129))

    with open(QUALITY_JSON, encoding="utf-8") as f:
        q = json.load(f)
    co = [x for x in q["missing"] if x["field"] == "CO"][0]
    checks.append(("CO 缺失数", int(co["missing"]), 20701))

    overall = pd.to_numeric(raw["PM2.5"], errors="coerce").mean()
    checks.append(("PM2.5 全量均值", round(float(overall), 4), 79.7934))

    ok = True
    for name, got, expect in checks:
        flag = "OK" if got == expect else "MISMATCH"
        if got != expect:
            ok = False
        print("  %-22s 实际=%-12s 期望=%-10s %s" % (name, got, expect, flag))
    return ok


def main():
    setup_font()
    check_inputs()
    os.makedirs(OUT_DIR, exist_ok=True)

    station, monthly, hourly = load_ads()
    raw = load_raw()

    print("开始生成图表 ...")
    fig_station(station)
    fig_monthly(monthly)
    fig_hourly(hourly)
    fig_missing()
    fig_season(raw)
    fig_corr(raw)

    ok = verify(station, monthly, hourly, raw)
    print("\n输出目录：", OUT_DIR)
    if not ok:
        raise SystemExit("存在数值不一致，请检查数据源")
    print("全部图表生成完毕，关键数值核对通过。")


if __name__ == "__main__":
    main()
