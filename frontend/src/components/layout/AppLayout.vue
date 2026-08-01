<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="brand">
        <span class="brand-title">{{ $t('CADD 分子对接平台') }}</span>
        <span class="brand-sub">{{ $t('本地计算 · 数据不出机') }}</span>
      </div>
      <el-menu
        mode="horizontal"
        router
        :default-active="activeMenu"
        :ellipsis="false"
        class="nav-menu"
      >
        <el-menu-item index="/">{{ $t('新建任务') }}</el-menu-item>
        <el-menu-item index="/tasks">{{ $t('任务队列') }}</el-menu-item>
        <el-menu-item index="/settings">{{ $t('软件配置') }}</el-menu-item>
        <el-menu-item index="/help">{{ $t('使用说明') }}</el-menu-item>
      </el-menu>
      <el-select :model-value="locale" size="small" class="lang-switch" @update:model-value="changeLocale">
        <el-option value="zh-CN" label="中文" />
        <el-option value="en" label="English" />
      </el-select>
    </header>

    <main class="app-main">
      <router-view />
    </main>

    <footer class="app-footer">
      {{ $t('本地分子对接可视化科研平台 · 所有分子数据仅存储于本机') }}
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setLocale } from '../../i18n'

const route = useRoute()
const { t, locale } = useI18n()

function changeLocale(value) {
  setLocale(value)
  const pageTitle = t(route.meta.title || '平台')
  document.title = `${pageTitle} | ${t('CADD 分子对接平台')}`
}

const activeMenu = computed(() => {
  if (route.path.startsWith('/result')) return '/tasks'
  if (route.path.startsWith('/tasks')) return '/tasks'
  if (route.path.startsWith('/settings')) return '/settings'
  if (route.path.startsWith('/help')) return '/help'
  return '/'
})
</script>

<style scoped>
.app-layout {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 20px;
  background: #0a101c;
  border-bottom: 1px solid var(--cadd-border);
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.brand-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--cadd-ink);
  letter-spacing: 0.2px;
}

.brand-sub {
  font-size: 12px;
  color: var(--cadd-muted);
}

.nav-menu {
  border-bottom: none;
}

.lang-switch {
  width: 110px;
  margin-left: 16px;
}

.app-main {
  flex: 1;
  width: 100%;
}

.app-footer {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--cadd-muted);
  font-size: 12px;
  border-top: 1px solid var(--cadd-border);
  background: #0a101c;
}
</style>
