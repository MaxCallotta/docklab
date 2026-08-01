<template>
  <el-config-provider :locale="elementLocale">
    <AppLayout />
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'
import AppLayout from './components/layout/AppLayout.vue'

const { locale } = useI18n()
const elementLocale = computed(() => (locale.value === 'en' ? en : zhCn))
</script>
