<template>
  <div class="page-shell">
    <div class="list-toolbar">
      <div>
        <h2 class="page-title">{{ $t('任务队列与历史') }}</h2>
        <div class="muted">{{ $t('全部任务记录保存在本地磁盘，支持重启失败任务与打包下载') }}</div>
      </div>
      <div class="toolbar-right">
        <el-select v-model="statusFilter" :placeholder="$t('全部状态')" clearable style="width: 130px" @change="reload">
          <el-option :label="$t('排队中')" value="queued" />
          <el-option :label="$t('运行中')" value="running" />
          <el-option :label="$t('已完成')" value="completed" />
          <el-option :label="$t('失败')" value="failed" />
        </el-select>
        <el-button type="primary" plain :loading="store.loading" @click="reload">{{ $t('刷新') }}</el-button>
        <el-button :disabled="!selectedRows.length" @click="batchDelete">{{ $t('批量删除') }}</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-table
        :data="store.tasks"
        v-loading="store.loading"
        @selection-change="(rows) => (selectedRows = rows)"
        :empty-text="$t('暂无本地任务')"
      >
        <el-table-column type="selection" width="46" />
        <el-table-column :label="$t('任务 ID')" width="110">
          <template #default="{ row }">
            <span class="mono task-id" :title="row.task_id">{{ row.task_id.slice(0, 8) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="$t('任务名称')" min-width="170" show-overflow-tooltip />
        <el-table-column :label="$t('配体文件')" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ ligandName(row) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('PDB 编号')" width="100">
          <template #default="{ row }">
            {{ pdbIdOf(row) || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('对接软件')" width="130">
          <template #default="{ row }">
            {{ engineName(row.engine_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('状态')" width="100">
          <template #default="{ row }">
            <StatusTag :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('总打分')" width="130" align="right">
          <template #default="{ row }">
            {{ formatAffinity(row.result_summary?.best_affinity) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('创建时间')" width="150">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('操作')" width="330" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewResult(row)">{{ $t('查看结果') }}</el-button>
            <el-button size="small" link @click="rerun(row)">{{ $t('重新运行') }}</el-button>
            <el-button size="small" link @click="download(row)">{{ $t('打包下载') }}</el-button>
            <el-button size="small" link type="danger" @click="removeTask(row)">{{ $t('删除') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'

import StatusTag from '../components/common/StatusTag.vue'
import { useTaskStore } from '../stores/task'
import { useSettingsStore } from '../stores/settings'
import { batchDelete as batchDeleteApi, deleteTask, downloadTaskUrl, restartTask } from '../api/task'
import { runDocking } from '../api/docking'
import { formatAffinity, formatTime } from '../utils/formatters'

const router = useRouter()
const store = useTaskStore()
const settings = useSettingsStore()
const { t } = useI18n()

const statusFilter = ref('')
const selectedRows = ref([])

const engineMap = computed(() => {
  const map = {}
  settings.engines.forEach((engine) => {
    map[engine.engine_id] = engine.engine_name
  })
  return map
})

function engineName(id) {
  return engineMap.value[id] || id || '-'
}

function ligandName(row) {
  return Object.keys(row.input_files || {}).find((k) => /\.(cdxml|sdf|mol2|txt|smi)$/i.test(k)) || row.name
}

function pdbIdOf(row) {
  return row.params?.pdb_id || row.params?.receptor_source_pdb_id || ''
}

function viewResult(row) {
  router.push(`/result/${row.task_id}`)
}

async function rerun(row) {
  await ElMessageBox.confirm(t('确认重新运行任务 {id}？', { id: row.task_id.slice(0, 8) }), t('重新运行'), {
    type: 'warning'
  })
  await restartTask(row.task_id)
  const p = row.params || {}
  if (p.receptor_path && p.ligand_path) {
    await runDocking({
      task_id: row.task_id,
      engine_id: row.engine_id || p.engine_id || 'vina',
      receptor_path: p.receptor_path,
      ligand_path: p.ligand_path,
      center_x: p.center_x ?? 0,
      center_y: p.center_y ?? 0,
      center_z: p.center_z ?? 0,
      size_x: p.size_x ?? 20,
      size_y: p.size_y ?? 20,
      size_z: p.size_z ?? 20,
      exhaustiveness: p.exhaustiveness ?? 8,
      energy_range: p.energy_range ?? 3,
      num_modes: p.num_modes ?? 9,
      seed: p.seed ?? null,
      cpu: p.cpu ?? null,
      timeout_seconds: p.timeout_seconds ?? 7200
    })
  }
  await reload()
  ElMessage.success(t('任务已重新提交'))
}

function download(row) {
  window.open(downloadTaskUrl(row.task_id), '_blank')
}

async function removeTask(row) {
  await ElMessageBox.confirm(t('删除任务 {id} 及其全部文件？', { id: row.task_id.slice(0, 8) }), t('删除任务'), {
    type: 'warning'
  })
  await deleteTask(row.task_id)
  await reload()
}

async function batchDelete() {
  await ElMessageBox.confirm(t('确认批量删除 {count} 个任务？', { count: selectedRows.value.length }), t('批量删除'), {
    type: 'warning'
  })
  await batchDeleteApi(selectedRows.value.map((row) => row.task_id))
  await reload()
}

async function reload() {
  await store.loadTasks(statusFilter.value || undefined)
}

watch(
  () => store.runningCount,
  (count) => {
    if (count > 0) store.startPolling()
    else store.stopPolling()
  }
)

onMounted(async () => {
  await Promise.all([settings.loadEngines(), reload()])
  if (store.runningCount > 0) store.startPolling()
})

onUnmounted(() => store.stopPolling())
</script>

<style scoped>
.list-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 12px;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.task-id {
  font-size: 12px;
  color: var(--cadd-muted);
}
</style>
