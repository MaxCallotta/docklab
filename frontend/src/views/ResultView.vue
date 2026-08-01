<template>
  <div class="page-shell">
    <div class="result-header">
      <div>
        <h2 class="page-title">{{ $t('对接结果分析') }}</h2>
        <div class="muted">
          {{ $t('任务 {id}', { id: taskId }) }} · <StatusTag :status="status" />
          <span v-if="task?.result_summary?.best_affinity !== undefined && task?.result_summary?.best_affinity !== null">
            {{ $t('最优打分') }} {{ formatAffinity(task.result_summary.best_affinity) }}
          </span>
        </div>
      </div>
      <el-progress
        v-if="status !== 'completed'"
        :percentage="progress"
        :status="status === 'failed' ? 'exception' : undefined"
        style="width: 240px"
      />
    </div>

    <el-alert
      v-if="status === 'failed'"
      type="error"
      :closable="false"
      show-icon
      :title="errorTitle"
      class="fail-alert"
    />

    <div class="result-grid">
      <section class="viewer-col">
        <SectionPanel :title="$t('对接体系 3D 预览')">
          <MoleculeViewer3D :files="previewFiles" height="600px" />
        </SectionPanel>
        <SectionPanel :title="$t('构象切换')">
          <div class="pose-selector">
            <span class="muted">{{ $t('当前构象') }}</span>
            <el-select v-model="currentPose" style="width: 180px" :disabled="!poses.length">
              <el-option
                v-for="pose in poses"
                :key="pose.index"
                :value="pose.index"
                :label="$t('构象 {index}  ({affinity} kcal/mol)', {
                  index: pose.index,
                  affinity: Number(pose.affinity).toFixed(2)
                })"
              />
            </el-select>
          </div>
        </SectionPanel>
      </section>

      <section class="table-col">
        <SectionPanel :title="$t('打分排序表')">
          <ScoreTable v-model="currentPose" :poses="poses" @select="onPoseSelect" />
          <div class="table-note muted">
            {{ $t('支持按结合自由能 / RMSD 升序降序排序，点击行或单选切换 3D 构象') }}
          </div>
        </SectionPanel>

        <SectionPanel :title="$t('导出与可视化')">
          <ExportActions
            :disabled="!poses.length"
            @export-pose="onExportPose"
            @generate-pml="onGeneratePml"
            @open-pymol="onOpenPymol"
            @export-csv="onExportCsv"
          />
        </SectionPanel>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import SectionPanel from '../components/common/SectionPanel.vue'
import StatusTag from '../components/common/StatusTag.vue'
import MoleculeViewer3D from '../components/molecule/MoleculeViewer3D.vue'
import ScoreTable from '../components/result/ScoreTable.vue'
import ExportActions from '../components/result/ExportActions.vue'
import { useTaskPolling } from '../composables/useTaskPolling'
import { exportPose, poseUrl, taskFileUrl } from '../api/task'
import { previewUrl } from '../api/molecule'
import { generatePml, openPymol } from '../api/visualization'
import { translateBackendMessage } from '../utils/backendMessages'
import { formatAffinity } from '../utils/formatters'

const route = useRoute()
const { t } = useI18n()
const taskId = String(route.params.taskId)
const taskIdRef = ref(taskId)
const { task, status, progress, start } = useTaskPolling(taskIdRef)

const currentPose = ref(1)

const poses = computed(() => task.value?.result_summary?.poses || [])
const errorTitle = computed(() => (
  task.value?.error_message
    ? translateBackendMessage(task.value.error_message)
    : t('任务执行失败')
))

const previewFiles = computed(() => {
  const files = []
  const receptorPath = task.value?.output_files?.receptor_pdbqt
  if (receptorPath) {
    files.push({ url: previewUrl(receptorPath), style: 'protein', label: 'receptor' })
  }
  if (poses.value.length && currentPose.value) {
    files.push({ url: poseUrl(taskId, currentPose.value), style: 'ligand', label: `pose-${currentPose.value}` })
  }
  return files
})

watch(
  poses,
  (list) => {
    if (list.length && !list.some((pose) => pose.index === currentPose.value)) {
      currentPose.value = list[0].index
    }
  },
  { immediate: true }
)

function onPoseSelect(index) {
  currentPose.value = index
}

async function onExportPose(format) {
  const result = await exportPose(taskId, currentPose.value, format)
  window.open(result.file_url, '_blank')
}

async function onGeneratePml() {
  const best = task.value?.result_summary?.best_affinity
  const result = await generatePml(taskId, best ?? null)
  ElMessage.success(t('PML 已生成：{path}', { path: result.pml_path }))
}

async function onOpenPymol() {
  const result = await openPymol(taskId)
  ElMessage.success(t('已唤起本地 PyMOL（进程 {pid}）', { pid: result.pid }))
}

function onExportCsv() {
  window.open(taskFileUrl(taskId, 'output', 'scores.csv'), '_blank')
}

start()
</script>

<style scoped>
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.fail-alert {
  margin-bottom: 12px;
}

.result-grid {
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  gap: 14px;
  align-items: start;
}

.pose-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-note {
  margin-top: 10px;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
