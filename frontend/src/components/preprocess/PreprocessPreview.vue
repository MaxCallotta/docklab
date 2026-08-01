<template>
  <div class="preprocess-preview">
    <div class="preview-header">
      <span class="preview-title">{{ file ? file.name : $t('暂无分子预览') }}</span>
      <div class="preview-tools">
        <el-button size="small" text :disabled="!file" @click="resetView">{{ $t('重置视角') }}</el-button>
        <el-button size="small" text :disabled="!file" @click="exportPng">{{ $t('导出PNG') }}</el-button>
      </div>
    </div>
    <div class="preview-body">
      <MoleculeViewer3D
        v-if="file"
        ref="viewerRef"
        :files="previewFiles"
        height="100%"
        :interactive="false"
      />
      <div v-else class="preview-empty muted">{{ $t('请先上传并处理分子') }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

import MoleculeViewer3D from '../molecule/MoleculeViewer3D.vue'

const props = defineProps({
  file: { type: Object, default: null }
})

const viewerRef = ref(null)

const previewFiles = computed(() => {
  if (!props.file?.url) return []
  return [{ url: props.file.url, style: 'ligand', label: props.file.name || 'molecule' }]
})

function resetView() {
  viewerRef.value?.resetView()
}

function exportPng() {
  viewerRef.value?.exportPng()
}
</script>

<style scoped>
.preprocess-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 360px;
  overflow: hidden;
  border: 1px solid rgba(96, 165, 250, 0.18);
  border-radius: 12px;
  background: rgba(10, 16, 28, 0.45);
  box-shadow: inset 0 0 34px rgba(0, 0, 0, 0.3);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(17, 25, 43, 0.6);
}

.preview-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
  color: var(--cadd-ink);
}

.preview-tools {
  display: flex;
  gap: 4px;
}

.preview-body {
  position: relative;
  flex: 1;
  min-height: 0;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 13px;
}
</style>
