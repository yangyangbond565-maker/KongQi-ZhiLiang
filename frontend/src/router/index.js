import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Query from '../views/Query.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/query', name: 'query', component: Query }
]

export default createRouter({
  history: createWebHashHistory(),
  routes
})
