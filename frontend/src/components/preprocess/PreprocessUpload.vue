<template>
  <div class="preprocess-upload">
    <el-upload
      drag
      multiple
      :accept="PREPROCESS_ACCEPT"
      :http-request="handleUpload"
      :show-file-list="false"
    >
      <div class="upload-main">{{ $t('点击或拖拽分子文件到此处') }}</div>
      <div class="upload-sub">{{ $t('支持 cdxml / sdf / mol2 / smi / pdbqt 格式') }}</div>
    </el-upload>

    <div v-if="files.length" class="file-list">
      <div v-for="file in files" :key="file.file_id" class="file-row">
        <span class="file-name">{{ file.filename }}</span>
        <span class="file-meta">{{ file.format }} · {{ formatSize(file.size) }}</span>
        <el-button size="small" text @click="$emit('remove', file.file_id)">{{ $t('删除') }}</el-button>
      </div>
      <div class="file-actions">
        <el-button size="small" text @click="$emit('clear')">{{ $t('清空全部') }}</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { uploadPreprocessFiles } from '../../api/preprocess'
import { PREPROCESS_ACCEPT, PREPROCESS_EXTENSIONS, MAX_UPLOAD_MB } from '../../utils/constants'
import { validateUploadFile } from '../../utils/validators'
import { translateBackendMessage } from '../../utils/backendMessages'

const { t } = useI18n()

const props = defineProps({
  files: { type: Array, default: () => [] },
  sessionId: { type: String, default: '' }
})

const emit = defineEmits(['session-change', 'add-files', 'remove', 'clear'])

function formatSize(size) {
  if (size == null) return '-'
  return size >= 1024 * 1024 ? `${(size / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(size / 1024))} KB`
}

async function handleUpload(options) {
  const file = options?.file
  if (!file || !validateUploadFile(file, PREPROCESS_EXTENSIONS, MAX_UPLOAD_MB)) {
    return
  }
  try {
    const data = await uploadPreprocessFiles([file], props.sessionId || undefined)
    emit('session-change', data.session_id)
    emit('add-files', data.files || [])
  } catch (error) {
    ElMessage.error(translateBackendMessage(error.message) || t('文件上传失败'))
  }
}
</script>

<style scoped>
.preprocess-upload {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload-main {
  font-size: 14px;
  color: var(--cadd-ink);
}

.upload-sub {
  margin-top: 6px;
  font-size: 12px;
  color: var(--cadd-muted);
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.025);
}

.file-name {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: var(--cadd-muted);
}

.file-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
