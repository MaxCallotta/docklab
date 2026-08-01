<template>
  <el-table
    :data="items"
    v-loading="loading"
    :empty-text="$t('暂无预处理结果')"
    :row-class-name="rowClassName"
    size="small"
  >
    <el-table-column type="index" :label="$t('序号')" width="60" />
    <el-table-column prop="filename" :label="$t('分子名称')" min-width="180" show-overflow-tooltip />
    <el-table-column prop="format" :label="$t('格式')" width="90" />
    <el-table-column :label="$t('处理状态')" width="110">
      <template #default="{ row }">
        <el-tag :type="statusType(row.status)" size="small" effect="plain">{{ statusLabel(row.status) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="properties.molecular_weight" :label="$t('分子量')" width="110" sortable align="right">
      <template #default="{ row }">{{ row.properties?.molecular_weight ?? '-' }}</template>
    </el-table-column>
    <el-table-column prop="properties.logp" label="logP" width="100" sortable align="right">
      <template #default="{ row }">{{ row.properties?.logp ?? '-' }}</template>
    </el-table-column>
    <el-table-column prop="error" :label="$t('失败原因')" min-width="180" show-overflow-tooltip>
      <template #default="{ row }">
        <span v-if="row.status === 'failed'" class="error-text">{{ row.error }}</span>
        <span v-else>-</span>
      </template>
    </el-table-column>
    <el-table-column :label="$t('操作')" width="200" fixed="right">
      <template #default="{ row }">
        <el-button size="small" link :disabled="row.status !== 'success'" @click="$emit('preview', row)">
          {{ $t('单个预览') }}
        </el-button>
        <el-button size="small" link :disabled="row.status !== 'success'" @click="$emit('download', row)">
          {{ $t('单个下载') }}
        </el-button>
        <el-button
          v-if="row.status === 'failed'"
          size="small"
          link
          type="primary"
          @click="$emit('retry', row)"
        >
          {{ $t('重试') }}
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['preview', 'download', 'retry'])

const { t } = useI18n()

function statusType(status) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'processing') return 'warning'
  return 'info'
}

function statusLabel(status) {
  return t({
    queued: '等待中',
    processing: '处理中',
    success: '成功',
    failed: '失败'
  }[status] || status)
}

function rowClassName({ row }) {
  return row.status === 'failed' ? 'preprocess-failed-row' : ''
}
</script>

<style scoped>
.error-text {
  color: var(--cadd-danger);
  font-size: 12px;
}
</style>

<style>
.el-table .preprocess-failed-row {
  background: rgba(248, 113, 113, 0.06) !important;
}
</style>
