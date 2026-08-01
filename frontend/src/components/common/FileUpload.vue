<template>
  <div class="file-upload">
    <el-upload
      ref="uploadEl"
      drag
      :accept="accept"
      :auto-upload="false"
      :limit="1"
      :on-change="handleChange"
      :on-exceed="handleExceed"
      :on-remove="handleRemove"
      :file-list="fileList"
    >
      <div class="upload-hint">
        <div class="upload-main">{{ hint }}</div>
        <div class="upload-sub">
          {{ $t('支持：{accept}，最大 {max} MB', { accept, max: maxSizeMB }) }}
        </div>
      </div>
    </el-upload>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { validateUploadFile } from '../../utils/validators'

const { t } = useI18n()

const props = defineProps({
  accept: { type: String, default: '.cdxml' },
  maxSizeMB: { type: Number, default: 200 },
  hint: { type: String, default: '点击或拖拽文件到此处' },
  extensions: { type: Array, default: () => [] }
})

const emit = defineEmits(['change', 'clear'])
const fileList = ref([])
const uploadEl = ref(null)

function allowedExtensions() {
  return props.extensions.length
    ? props.extensions
    : props.accept.split(',').map((s) => s.trim().toLowerCase())
}

function handleChange(uploadFile) {
  const raw = uploadFile?.raw
  if (!raw || !validateUploadFile(raw, allowedExtensions(), props.maxSizeMB)) {
    fileList.value = []
    return
  }
  fileList.value = [uploadFile]
  emit('change', raw)
}

function handleExceed(files) {
  const rawFile = files?.[0]
  if (!rawFile || !validateUploadFile(rawFile, allowedExtensions(), props.maxSizeMB)) {
    return
  }
  uploadEl.value?.handleStart(rawFile)
}

function clear() {
  fileList.value = []
  emit('clear')
}

function handleRemove() {
  clear()
  ElMessage.info(t('已移除文件'))
}

defineExpose({ clear })
</script>

<style scoped>
.upload-hint {
  padding: 14px 8px;
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
</style>
