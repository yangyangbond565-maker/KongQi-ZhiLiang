<template>
  <div class="query-page">
    <header class="page-header">
      <div>
        <h2>统计查询</h2>
        <p class="subtitle">数据来自后端统计结果表，按污染物筛选</p>
      </div>
      <div class="filter-box">
        <label for="q-pollutant">污染物</label>
        <select id="q-pollutant" v-model="pollutant" class="pollutant-select">
          <option v-for="p in pollutants" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
    </header>

    <div v-if="error" class="error-bar">{{ error }}</div>

    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}（{{ rowsOf(tab.key).length }}）
      </button>
    </div>

    <div class="panel">
      <div v-if="loading" class="empty-tip">加载中...</div>
      <template v-else>
        <div v-if="!pagedRows.length" class="empty-tip">暂无数据</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th v-for="col in currentColumns" :key="col.key">{{ col.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in pagedRows" :key="idx">
              <td v-for="col in currentColumns" :key="col.key">
                {{ formatCell(row, col) }}
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="totalPages > 1" class="pager">
          <button :disabled="page === 1" @click="page = page - 1">上一页</button>
          <span>第 {{ page }} / {{ totalPages }} 页</span>
          <button :disabled="page === totalPages" @click="page = page + 1">下一页</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { POLLUTANTS, fetchStations, fetchMonthly, fetchHourly } from '../api'

const pollutants = POLLUTANTS
const pollutant = ref('PM2.5')
const activeTab = ref('station')
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const error = ref('')

const stations = ref([])
const monthly = ref([])
const hourly = ref([])

const tabs = [
  { key: 'station', label: '站点统计' },
  { key: 'monthly', label: '月度统计' },
  { key: 'hourly', label: '小时统计' }
]

const columnsMap = {
  station: [
    { key: 'station', label: '监测站点' },
    { key: 'pollutant', label: '污染物' },
    { key: 'avgValue', label: '平均浓度(μg/m³)' },
    { key: 'validCnt', label: '有效样本数' }
  ],
  monthly: [
    { key: 'obsYear', label: '年份' },
    { key: 'obsMonth', label: '月份' },
    { key: 'pollutant', label: '污染物' },
    { key: 'avgValue', label: '平均浓度(μg/m³)' },
    { key: 'validCnt', label: '有效样本数' }
  ],
  hourly: [
    { key: 'obsHour', label: '小时' },
    { key: 'pollutant', label: '污染物' },
    { key: 'avgValue', label: '平均浓度(μg/m³)' },
    { key: 'validCnt', label: '有效样本数' }
  ]
}

const currentColumns = computed(() => columnsMap[activeTab.value])

function rowsOf(tab) {
  if (tab === 'station') return stations.value
  if (tab === 'monthly') return monthly.value
  return hourly.value
}

const currentRows = computed(() => rowsOf(activeTab.value))
const totalPages = computed(() => Math.max(1, Math.ceil(currentRows.value.length / pageSize)))
const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return currentRows.value.slice(start, start + pageSize)
})

function formatCell(row, col) {
  const v = row[col.key]
  if (v === null || v === undefined) return '—'
  if (col.key === 'validCnt') return Number(v).toLocaleString('zh-CN')
  return v
}

function switchTab(key) {
  activeTab.value = key
  page.value = 1
}

async function loadData() {
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
    page.value = 1
  } catch (e) {
    error.value = '查询失败：' + e.message
    stations.value = []
    monthly.value = []
    hourly.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
watch(pollutant, loadData)
</script>

<style scoped>
.query-page { padding: 18px 24px 32px; }

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
}

.page-header h2 { margin: 0; font-size: 22px; color: #7fd4ff; }
.subtitle { margin: 6px 0 0; font-size: 13px; color: #7fa6c8; }
.filter-box { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #9fc6e8; }

.tabs { display: flex; gap: 10px; margin-bottom: 12px; }

.tab-btn {
  background: rgba(10, 34, 61, 0.7);
  color: #9fc6e8;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 4px;
  padding: 7px 16px;
  cursor: pointer;
  font-size: 13px;
}

.tab-btn.active {
  background: #38bdf8;
  color: #04121f;
  border-color: #38bdf8;
  font-weight: 600;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
  font-size: 13px;
  color: #9fc6e8;
}

.pager button {
  background: rgba(56, 189, 248, 0.12);
  color: #bfe6ff;
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 4px;
  padding: 5px 12px;
  cursor: pointer;
}

.pager button:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
