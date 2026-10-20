<template>
  <div class="app">
    <nav class="topnav">
      <span class="brand">城市空气质量大数据分析与可视化系统</span>
      <div class="links">
        <router-link to="/">数据大屏</router-link>
        <router-link to="/query">统计查询</router-link>
      </div>
    </nav>
    <router-view />
  </div>
</template>
