<template>
  <div ref="el" class="chart-box"></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true }
})

const el = ref(null)
let chart = null

function resize() {
  if (chart) chart.resize()
}

onMounted(() => {
  chart = echarts.init(el.value)
  chart.setOption(props.option)
  window.addEventListener('resize', resize)
})

watch(
  () => props.option,
  (val) => {
    if (chart) chart.setOption(val, true)
  },
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.chart-box {
  width: 100%;
  height: 100%;
  min-height: 280px;
}
</style>
