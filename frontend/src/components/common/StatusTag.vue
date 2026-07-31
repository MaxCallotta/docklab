<template>
  <el-tag :type="statusMeta.type" size="small" effect="plain">
    {{ statusMeta.label }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'
import { STATUS_MAP } from '../../utils/constants'

const props = defineProps({
  status: { type: String, default: 'queued' }
})

const statusMeta = computed(() => STATUS_MAP[props.status] || { label: props.status, type: 'info' })
</script>
