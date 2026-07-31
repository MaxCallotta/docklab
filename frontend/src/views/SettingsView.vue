<template>
  <div class="page-shell">
    <h2 class="page-title">软件配置管理</h2>
    <div class="settings-grid">
      <section>
        <SectionPanel title="本地软件路径">
          <el-form label-width="150px">
            <el-form-item label="AutoDock Vina">
              <el-input v-model="form.vina_bin" placeholder="vina.exe 完整路径" />
            </el-form-item>
            <el-form-item label="AutoDock 4">
              <el-input v-model="form.autodock4_bin" placeholder="autodock4.exe（预留）" />
            </el-form-item>
            <el-form-item label="AutoGrid 4">
              <el-input v-model="form.autogrid4_bin" placeholder="autogrid4.exe（预留）" />
            </el-form-item>
            <el-form-item label="PyMOL">
              <el-input v-model="form.pymol_bin" placeholder="pymol.exe 完整路径" />
            </el-form-item>
            <el-form-item label="OpenBabel">
              <el-input v-model="form.obabel_bin" placeholder="obabel.exe 完整路径" />
            </el-form-item>
          </el-form>

          <el-divider content-position="left">预留对接软件路径</el-divider>
          <!-- EXTENSION-POINT：新增对接软件时，在此追加 engine_id/path 输入项，
               提交到 POST /api/v1/system/config 的 extra_engines -->
          <div v-for="engine in form.extra_engines" :key="engine.engine_id" class="extra-engine">
            <el-input v-model="engine.path" :placeholder="`${engine.engine_name} 可执行路径`" />
          </div>
        </SectionPanel>
      </section>

      <section>
        <SectionPanel title="全局预处理默认值">
          <el-form label-width="150px">
            <el-form-item label="加氢">
              <el-switch v-model="form.add_hydrogens" active-text="自动补氢" />
            </el-form-item>
            <el-form-item label="电荷计算方法">
              <el-select v-model="form.charge_method" style="width: 100%">
                <el-option label="Gasteiger" value="gasteiger" />
                <el-option label="MMFF94" value="mmff94" />
              </el-select>
            </el-form-item>
            <el-form-item label="pH 值">
              <el-input-number v-model="form.ph" :min="0" :max="14" :precision="1" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-form>
        </SectionPanel>

        <SectionPanel title="环境检测">
          <el-table :data="engineStatus" size="small">
            <el-table-column prop="engine_name" label="软件" />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.available ? 'success' : 'danger'" size="small" effect="plain">
                  {{ row.available ? '可用' : '不可用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="路径" show-overflow-tooltip />
          </el-table>
        </SectionPanel>

        <div class="save-bar">
          <el-button type="primary" :loading="saving" @click="saveAll">保存全部配置</el-button>
        </div>
      </section>
    </div>

    <SectionPanel title="参数模板管理">
      <div class="template-toolbar">
        <el-button type="primary" plain @click="templateDialog = true">新增模板</el-button>
      </div>
      <el-table :data="settings.templates" empty-text="暂无模板">
        <el-table-column prop="name" label="模板名称" min-width="200" />
        <el-table-column label="参数摘要" min-width="320" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="mono template-summary">{{ summarizeParams(row.params) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="loadTemplate(row)">加载</el-button>
            <el-button size="small" link type="danger" @click="removeTemplate(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </SectionPanel>

    <SectionPanel title="本地日志">
      <div class="log-toolbar">
        <el-date-picker
          v-model="logDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
          style="width: 160px"
        />
        <el-select v-model="logLevel" clearable placeholder="全部级别" style="width: 130px">
          <el-option label="INFO" value="INFO" />
          <el-option label="WARNING" value="WARNING" />
          <el-option label="ERROR" value="ERROR" />
        </el-select>
        <el-button type="primary" plain :loading="logLoading" @click="loadLogs">刷新日志</el-button>
      </div>
      <el-table :data="logEntries" size="small" max-height="460" empty-text="暂无日志">
        <el-table-column prop="time" label="时间" width="165" />
        <el-table-column label="级别" width="90">
          <template #default="{ row }">
            <el-tag :type="logTagType(row.level)" size="small" effect="plain">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
        <el-table-column prop="task_id" label="任务 ID" width="120" show-overflow-tooltip />
        <el-table-column prop="command" label="执行命令" min-width="240" show-overflow-tooltip />
        <el-table-column prop="source_file" label="输入文件" width="160" show-overflow-tooltip />
        <el-table-column prop="error_stack" label="错误堆栈" min-width="260" show-overflow-tooltip />
      </el-table>
    </SectionPanel>

    <el-dialog v-model="templateDialog" title="保存参数模板" width="440px">
      <el-form label-width="90px">
        <el-form-item label="模板名称" required>
          <el-input v-model="templateName" placeholder="例如：ATP 口袋-默认盒子" />
        </el-form-item>
        <el-form-item label="参数 JSON">
          <el-input v-model="templateParamsJson" type="textarea" :rows="6" class="mono" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="templateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplateFromJson">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import SectionPanel from '../components/common/SectionPanel.vue'
import { useSettingsStore } from '../stores/settings'
import { deleteTemplate, getLogs, saveConfig, saveTemplate } from '../api/system'
import { PARAMS_DEFAULTS } from '../utils/constants'

const router = useRouter()
const settings = useSettingsStore()

const saving = ref(false)
const templateDialog = ref(false)
const templateName = ref('')
const templateParamsJson = ref(JSON.stringify(PARAMS_DEFAULTS, null, 2))
const logDate = ref(new Date().toISOString().slice(0, 10))
const logLevel = ref('')
const logEntries = ref([])
const logLoading = ref(false)

const form = reactive({
  vina_bin: '',
  autodock4_bin: '',
  autogrid4_bin: '',
  pymol_bin: '',
  obabel_bin: '',
  extra_engines: [],
  add_hydrogens: true,
  charge_method: 'gasteiger',
  ph: 7.4
})

const engineStatus = computed(() => {
  const env = settings.environment || {}
  return [
    { engine_name: 'AutoDock Vina', available: Boolean(env.vina), path: env.vina || '' },
    { engine_name: 'PyMOL', available: Boolean(env.pymol), path: env.pymol || '' },
    { engine_name: 'OpenBabel', available: Boolean(env.obabel), path: env.obabel || '' },
    { engine_name: 'AutoDock 4', available: Boolean(env.autodock4), path: env.autodock4 || '' },
    { engine_name: 'AutoGrid 4', available: Boolean(env.autogrid4), path: env.autogrid4 || '' }
  ]
})

onMounted(async () => {
  await settings.loadAll()
  await loadLogs()
  const env = settings.environment || {}
  const config = settings.config || {}
  const paths = config.engine_paths || {}
  form.vina_bin = paths.vina_bin || env.vina || ''
  form.autodock4_bin = paths.autodock4_bin || env.autodock4 || ''
  form.autogrid4_bin = paths.autogrid4_bin || env.autogrid4 || ''
  form.pymol_bin = config.pymol_bin || env.pymol || ''
  form.obabel_bin = paths.obabel_bin || env.obabel || ''
  form.extra_engines = (config.extra_engines || []).map((item) => ({ ...item }))
  const defaults = config.global_defaults || {}
  form.add_hydrogens = defaults.add_hydrogens ?? true
  form.charge_method = defaults.charge_method || 'gasteiger'
  form.ph = defaults.ph ?? 7.4
})

async function saveAll() {
  saving.value = true
  try {
    await saveConfig({
      engine_paths: {
        vina_bin: form.vina_bin,
        autodock4_bin: form.autodock4_bin,
        autogrid4_bin: form.autogrid4_bin,
        obabel_bin: form.obabel_bin
      },
      pymol_bin: form.pymol_bin,
      extra_engines: form.extra_engines,
      global_defaults: {
        add_hydrogens: form.add_hydrogens,
        charge_method: form.charge_method,
        ph: form.ph
      }
    })
    await settings.loadEnvironment()
    ElMessage.success('配置已保存，重启后端服务后生效')
  } finally {
    saving.value = false
  }
}

function summarizeParams(params) {
  const p = params || {}
  return `engine=${p.engine_id || '-'} center=(${p.center_x ?? 0},${p.center_y ?? 0},${p.center_z ?? 0}) size=(${p.size_x ?? 20},${p.size_y ?? 20},${p.size_z ?? 20}) exhaust=${p.exhaustiveness ?? 8}`
}

function loadTemplate(row) {
  settings.loadedParams = { ...row.params }
  ElMessage.success('参数模板已加载，正在前往新建任务页')
  router.push('/')
}

async function removeTemplate(row) {
  await ElMessageBox.confirm(`删除模板「${row.name}」？`, '删除模板', { type: 'warning' })
  await deleteTemplate(row.name)
  await settings.loadTemplates()
}

async function saveTemplateFromJson() {
  if (!templateName.value.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  let parsed
  try {
    parsed = JSON.parse(templateParamsJson.value)
  } catch {
    ElMessage.error('参数 JSON 格式不正确')
    return
  }
  await saveTemplate({ name: templateName.value.trim(), params: parsed })
  templateDialog.value = false
  await settings.loadTemplates()
  ElMessage.success('模板已保存')
}

async function loadLogs() {
  logLoading.value = true
  try {
    const data = await getLogs({
      date: logDate.value,
      level: logLevel.value || undefined,
      limit: 300
    })
    logEntries.value = data.entries || []
  } finally {
    logLoading.value = false
  }
}

function logTagType(level) {
  if (level === 'ERROR') return 'danger'
  if (level === 'WARNING') return 'warning'
  return 'info'
}
</script>

<style scoped>
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  align-items: start;
}

.extra-engine {
  margin-bottom: 8px;
}

.save-bar {
  margin-top: 10px;
  text-align: right;
}

.template-toolbar {
  margin-bottom: 10px;
}

.template-summary {
  font-size: 12px;
  color: var(--cadd-muted);
}

.log-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

@media (max-width: 1100px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
