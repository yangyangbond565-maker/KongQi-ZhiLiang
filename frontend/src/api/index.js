import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 15000
})

http.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && body.code !== 0) {
      return Promise.reject(new Error(body.message || '接口返回错误'))
    }
    return body.data
  },
  (err) => {
    let msg = '请求失败'
    if (err.response) {
      const body = err.response.data
      msg = (body && body.message) ? body.message : ('HTTP ' + err.response.status)
    } else if (err.code === 'ECONNABORTED') {
      msg = '请求超时，请检查后端是否启动'
    } else {
      msg = '无法连接后端服务'
    }
    return Promise.reject(new Error(msg))
  }
)

export const POLLUTANTS = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']

export function fetchOverview() {
  return http.get('/overview')
}

export function fetchStations(pollutant) {
  return http.get('/stations', { params: { pollutant } })
}

export function fetchMonthly(pollutant) {
  return http.get('/monthly', { params: { pollutant } })
}

export function fetchHourly(pollutant) {
  return http.get('/hourly', { params: { pollutant } })
}
