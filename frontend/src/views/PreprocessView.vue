<template>
  <div class="page-shell preprocess-page">
    <h2 class="page-title">{{ $t('分子预处理工具箱') }}</h2>

    <div class="preprocess-grid">
      <section class="pp-left">
        <SectionPanel :title="$t('分子文件上传')">
          <PreprocessUpload
            :files="files"
            :session-id="sessionId"
            @session-change="sessionId = $event"
            @add-files="addFiles"
            @remove="removeFile"
            @clear="clearFiles"
          />
        </SectionPanel>

        <SectionPanel :title="$t('处理选项')">
          <PreprocessOptions v-model="options" />
        </SectionPanel>

        <SectionPanel :title="$t('输出设置与执行')">
          <PreprocessOutput
            v-model:output-format="outputFormat"
            :loading="running || loading"
            :disabled="!files.length"
            @run="handleRun"
          />
        </SectionPanel>
      </section>

      <section class="pp-right">
        <SectionPanel :title="$t('3D 分子预览')">
          <PreprocessPreview :file="currentPreview" />
        </SectionPanel>
        <SectionPanel :title="$t('处理结果')">
          <PreprocessResults
            :items="items"
            :loading="running || loading"
            @preview="preview"
            @download="download"
            @retry="retry"
          />
        </SectionPanel>
      </section>
    </div>

    <div class="batch-bar">
      <div class="batch-left">
        <el-checkbox :model-value="allSelected" @change="toggleAll">
          {{ $t('全选') }}
        </el-checkbox>
        <el-button size="small" text @click="invertSelection">{{ $t('反选') }}</el-button>
        <el-button size="small" :disabled="!selectedIds.length" @click="downloadSelected">
          {{ $t('批量下载') }}
        </el-button>
        <el-button size="small" :disabled="!selectedIds.length" @click="deleteSelected">
          {{ $t('批量删除') }}
        </el-button>
        <el-button size="small" :disabled="!items.length" @click="clearResults">
          {{ $t('清空结果') }}
        </el-button>
      </div>
      <div class="batch-right">
        <el-progress :percentage="progressPercent" :stroke-width="8" style="width: 220px" />
        <span class="muted">{{ $t('已完成') }} {{ successCount }} / {{ items.length }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import SectionPanel from '../components/common/SectionPanel.vue'
import PreprocessUpload from '../components/preprocess/PreprocessUpload.vue'
import PreprocessOptions from '../components/preprocess/PreprocessOptions.vue'
import PreprocessOutput from '../components/preprocess/PreprocessOutput.vue'
import PreprocessPreview from '../components/preprocess/PreprocessPreview.vue'
import PreprocessResults from '../components/preprocess/PreprocessResults.vue'
import {
  getPreprocessStatus,
  preprocessBatchDownloadUrl,
  preprocessDownloadUrl,
  runPreprocess
} from '../api/preprocess'
import { translateBackendMessage } from '../utils/backendMessages'

const { t } = useI18n()

const files = ref([])
const sessionId = ref('')
const options = reactive({
  add_hydrogens: false,
  compute_gasteiger: false,
  remove_salts: false,
  remove_duplicates: false,
  enable_conformations: false,
  num_conformations: 1,
  compute_properties: true,
  ph: 7.4
})
const outputFormat = ref('sdf')
const batchId = ref('')
const items = ref([])
const running = ref(false)
const loading = ref(false)
const currentPreview = ref(null)
const selectedIds = ref([])

let pollTimer = null

const successCount = computed(() => items.value.filter((item) => item.status === 'success').length)
const failedCount = computed(() => items.value.filter((item) => item.status === 'failed').length)
const progressPercent = computed(() => {
  if (!items.value.length) return 0
  return Math.round(((successCount.value + failedCount.value) / items.value.length) * 100)
})
const allSelected = computed(
  () => items.value.length > 0 && selectedIds.value.length === items.value.length
)

function addFiles(records) {
  const existing = new Set(files.value.map((file) => file.file_id))
  records.forEach((record) => {
    if (!existing.has(record.file_id)) {
      files.value.push(record)
    }
  })
}

function removeFile(fileId) {
  files.value = files.value.filter((file) => file.file_id !== fileId)
  selectedIds.value = selectedIds.value.filter((id) => id !== fileId)
}

function clearFiles() {
  files.value = []
  sessionId.value = ''
  selectedIds.value = []
}

async function handleRun() {
  if (!files.value.length) {
    ElMessage.warning(t('请先上传分子文件'))
    return
  }
  loading.value = true
  try {
    const data = await runPreprocess({
      session_id: sessionId.value,
      file_ids: files.value.map((file) => file.file_id),
      options: { ...options },
      output_format: outputFormat.value
    })
    batchId.value = data.batch_id
    await pollStatus(data.batch_id)
  } catch (error) {
    ElMessage.error(translateBackendMessage(error.message) || t('预处理任务提交失败'))
  } finally {
    loading.value = false
  }
}

async function pollStatus(id) {
  running.value = true
  clearInterval(pollTimer)
  await refreshStatus(id)
  pollTimer = setInterval(() => refreshStatus(id), 1200)
}

async function refreshStatus(id) {
  try {
    const data = await getPreprocessStatus(id)
    const next = (data.items || []).map((item) => ({
      ...item,
      url: item.output_path ? preprocessDownloadUrl(item.file_id, item.output_name || 'result.sdf') : ''
    }))
    items.value = next
    if (!currentPreview.value) {
      const firstSuccess = next.find((item) => item.status === 'success')
      if (firstSuccess) {
        currentPreview.value = {
          file_id: firstSuccess.file_id,
          name: firstSuccess.output_name || firstSuccess.filename,
          url: firstSuccess.url
        }
      }
    }
    if (data.status === 'completed') {
      running.value = false
      clearInterval(pollTimer)
      pollTimer = null
    }
  } catch {
    running.value = false
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function preview(item) {
  currentPreview.value = {
    file_id: item.file_id,
    name: item.output_name || item.filename,
    url: preprocessDownloadUrl(item.file_id, item.output_name || 'result.sdf')
  }
}

function download(item) {
  window.open(preprocessDownloadUrl(item.file_id, item.output_name || 'result.sdf'), '_blank')
}

async function retry(item) {
  loading.value = true
  try {
    const data = await runPreprocess({
      session_id: sessionId.value,
      file_ids: [item.file_id],
      options: { ...options },
      output_format: outputFormat.value
    })
    await pollStatus(data.batch_id)
  } catch (error) {
    ElMessage.error(translateBackendMessage(error.message) || t('重试失败'))
  } finally {
    loading.value = false
  }
}

function toggleAll(checked) {
  selectedIds.value = checked ? items.value.map((item) => item.file_id) : []
}

function invertSelection() {
  const current = new Set(selectedIds.value)
  selectedIds.value = items.value
    .map((item) => item.file_id)
    .filter((id) => !current.has(id))
}

function downloadSelected() {
  if (batchId.value) {
    window.open(preprocessBatchDownloadUrl(batchId.value), '_blank')
  }
}

function deleteSelected() {
  items.value = items.value.filter((item) => !selectedIds.value.includes(item.file_id))
  selectedIds.value = []
}

function clearResults() {
  items.value = []
  selectedIds.value = []
  currentPreview.value = null
  batchId.value = ''
  running.value = false
  clearInterval(pollTimer)
  pollTimer = null
}

onBeforeUnmount(() => {
  clearInterval(pollTimer)
})
</script>

<style scoped>
.preprocess-grid {
  display: grid;
  grid-template-columns: 40% 60%;
  gap: 14px;
  align-items: start;
}

.pp-left,
.pp-right {
  min-width: 0;
}

.pp-left {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.pp-right {
  display: grid;
  grid-template-rows: 1.5fr 1fr;
  gap: 14px;
  min-height: 640px;
}

.batch-bar {
  position: sticky;
  bottom: 10px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(15, 23, 40, 0.82);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(12px);
}

.batch-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.batch-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

@media (max-width: 1100px) {
  .preprocess-grid {
    grid-template-columns: 1fr;
  }
}
</style>
