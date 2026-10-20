<template>
  <div class="dashboard">
    <header class="screen-header">
      <div>
        <h1>城市空气质量大数据分析与可视化系统</h1>
        <p class="subtitle">
          北京市 12 个监测站点 · 历史数据
          <span v-if="overview">{{ overview.startMonth }} 至 {{ overview.endMonth }}</span>
        </p>
      </div>
      <div class="filter-box">
        <label for="pollutant">污染物</label>
        <select id="pollutant" v-model="pollutant" class="pollutant-select">
          <option v-for="p in pollutants" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
    </header>

    <div v-if="error" class="error-bar">{{ error }}</div>

    <section class="cards">
      <div class="card">
        <div class="card-label">监测站点数量</div>
        <div class="card-value">{{ overview ? overview.stationCount : '--' }}</div>
        <div class="card-unit">个站点</div>
      </div>
      <div class="card">
        <div class="card-label">污染物种类</div>
        <div class="card-value">{{ overview ? overview.pollutantCount : '--' }}</div>
        <div class="card-unit">种污染物</div>
      </div>
      <div class="card">
        <div class="card-label">PM2.5 有效样本</div>
        <div class="card-value">{{ overview ? formatNum(overview.pm25ValidSamples) : '--' }}</div>
        <div class="card-unit">条非空观测</div>
      </div>
      <div class="card">
        <div class="card-label">数据覆盖时间</div>
        <div class="card-value small">
          {{ overview ? overview.startMonth + ' ~ ' + overview.endMonth : '--' }}
        </div>
        <div class="card-unit">历史数据，非实时</div>
      </div>
    </section>

    <section class="chart-grid">
      <div class="panel chart-wide">
        <h3 class="panel-title">各监测站点 {{ pollutant }} 平均浓度（μg/m³）</h3>
        <div class="chart-wrap">
          <BaseChart v-if="stationOption" :option="stationOption" />
          <div v-if="loading" class="loading-mask">加载中...</div>
        </div>
      </div>

      <div class="panel">
        <h3 class="panel-title">月度 {{ pollutant }} 平均浓度（μg/m³）</h3>
        <div class="chart-wrap">
          <BaseChart v-if="monthlyOption" :option="monthlyOption" />
        </div>
      </div>

      <div class="panel">
        <h3 class="panel-title">24 小时 {{ pollutant }} 浓度变化（μg/m³）</h3>
        <div class="chart-wrap">
          <BaseChart v-if="hourlyOption" :option="hourlyOption" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import { POLLUTANTS, fetchOverview, fetchStations, fetchMonthly, fetchHourly } from '../api'

const pollutants = POLLUTANTS
const pollutant = ref('PM2.5')
const overview = ref(null)
const stations = ref([])
const monthly = ref([])
const hourly = ref([])
const loading = ref(false)
const error = ref('')

const axisStyle = {
  axisLine: { lineStyle: { color: 'rgba(143, 212, 255, 0.35)' } },
  axisLabel: { color: '#9fc6e8', fontSize: 11 },
  splitLine: { lineStyle: { color: 'rgba(143, 212, 255, 0.12)' } }
}

const tooltipStyle = {
  backgroundColor: 'rgba(6, 24, 44, 0.95)',
  borderColor: 'rgba(56, 189, 248, 0.5)',
  textStyle: { color: '#d7e9ff', fontSize: 12 }
}

function formatNum(n) {
  if (n === null || n === undefined) return '--'
  return Number(n).toLocaleString('zh-CN')
}

const stationOption = computed(() => {
  if (!stations.value.length) return null
  return {
    grid: { left: 55, right: 20, top: 30, bottom: 70 },
    tooltip: {
      trigger: 'axis',
      ...tooltipStyle,
      formatter: (params) => {
        const p = params[0]
        const row = stations.value[p.dataIndex]
        return p.name + '<br/>平均浓度：' + p.value + ' μg/m³<br/>有效样本：' + formatNum(row.validCnt)
      }
    },
    xAxis: {
      type: 'category',
      data: stations.value.map((i) => i.station),
      axisLabel: { ...axisStyle.axisLabel, rotate: 35 },
      axisLine: axisStyle.axisLine
    },
    yAxis: {
      type: 'value',
      name: 'μg/m³',
      nameTextStyle: { color: '#9fc6e8' },
      axisLabel: axisStyle.axisLabel,
      splitLine: axisStyle.splitLine
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 32,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#38bdf8' },
              { offset: 1, color: 'rgba(56, 189, 248, 0.25)' }
            ]
          }
        },
        data: stations.value.map((i) => i.avgValue)
      }
    ]
  }
})

const monthlyOption = computed(() => {
  if (!monthly.value.length) return null
  return {
    grid: { left: 55, right: 20, top: 30, bottom: 55 },
    tooltip: {
      trigger: 'axis',
      ...tooltipStyle,
      formatter: (params) => {
        const p = params[0]
        const row = monthly.value[p.dataIndex]
        return p.name + '<br/>平均浓度：' + p.value + ' μg/m³<br/>有效样本：' + formatNum(row.validCnt)
      }
    },
    xAxis: {
      type: 'category',
      data: monthly.value.map((i) => i.obsYear + '-' + String(i.obsMonth).padStart(2, '0')),
      axisLabel: { ...axisStyle.axisLabel, rotate: 40 },
      axisLine: axisStyle.axisLine
    },
    yAxis: {
      type: 'value',
      name: 'μg/m³',
      nameTextStyle: { color: '#9fc6e8' },
      axisLabel: axisStyle.axisLabel,
      splitLine: axisStyle.splitLine
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: '#22d3ee' },
        itemStyle: { color: '#22d3ee' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(34, 211, 238, 0.35)' },
              { offset: 1, color: 'rgba(34, 211, 238, 0.02)' }
            ]
          }
        },
        data: monthly.value.map((i) => i.avgValue)
      }
    ]
  }
})

const hourlyOption = computed(() => {
  if (!hourly.value.length) return null
  return {
    grid: { left: 55, right: 20, top: 30, bottom: 40 },
    tooltip: {
      trigger: 'axis',
      ...tooltipStyle,
      formatter: (params) => {
        const p = params[0]
        const row = hourly.value[p.dataIndex]
        return p.name + '<br/>平均浓度：' + p.value + ' μg/m³<br/>有效样本：' + formatNum(row.validCnt)
      }
    },
    xAxis: {
      type: 'category',
      data: hourly.value.map((i) => i.obsHour + '时'),
      axisLabel: axisStyle.axisLabel,
      axisLine: axisStyle.axisLine
    },
    yAxis: {
      type: 'value',
      name: 'μg/m³',
      nameTextStyle: { color: '#9fc6e8' },
      axisLabel: axisStyle.axisLabel,
      splitLine: axisStyle.splitLine
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: '#a78bfa' },
        itemStyle: { color: '#a78bfa' },
        data: hourly.value.map((i) => i.avgValue)
      }
    ]
  }
})

async function loadOverview() {
  try {
    overview.value = await fetchOverview()
  } catch (e) {
    error.value = '概览数据加载失败：' + e.message
  }
}

async function loadCharts() {
  loading.value = true
  error.value = ''
  try {
    const [s, m, h] = await Promise.all([
      fetchStations(pollutant.value),
      fetchMonthly(pollutant.value),
      fetchHourly(pollutant.value)
    ])
    stations.value = s
    monthly.value = m
    hourly.value = h
  } catch (e) {
    error.value = '图表数据加载失败：' + e.message
    stations.value = []
    monthly.value = []
    hourly.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOverview()
  loadCharts()
})

watch(pollutant, () => {
  loadCharts()
})
</script>

<style scoped>
.dashboard { padding: 18px 24px 32px; }

.screen-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.screen-header h1 {
  margin: 0;
  font-size: 24px;
  letter-spacing: 2px;
  color: #7fd4ff;
  text-shadow: 0 0 18px rgba(56, 189, 248, 0.45);
}

.subtitle { margin: 6px 0 0; font-size: 13px; color: #7fa6c8; }

.filter-box { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #9fc6e8; }

.cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.card {
  background: linear-gradient(160deg, rgba(12, 42, 74, 0.9), rgba(6, 22, 40, 0.9));
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: 8px;
  padding: 14px 16px;
  box-shadow: inset 0 0 24px rgba(56, 189, 248, 0.08);
}

.card-label { font-size: 13px; color: #8fd4ff; }

.card-value {
  font-size: 30px;
  font-weight: 700;
  color: #e6f6ff;
  margin: 8px 0 4px;
  font-family: Consolas, "Microsoft YaHei", monospace;
}

.card-value.small { font-size: 20px; }
.card-unit { font-size: 12px; color: #6b8cab; }

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.chart-wide { grid-column: 1 / -1; }

.chart-wrap { position: relative; height: 320px; }
.chart-wide .chart-wrap { height: 340px; }

.loading-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(3, 10, 20, 0.55);
  color: #8fd4ff;
  font-size: 14px;
}

@media (max-width: 1200px) {
  .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .chart-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
