<template>
  <div class="page-shell">
    <div class="home-grid">
      <!-- 左栏：上传区（置顶）+ 盒子画布/参数区（隔离在下方） -->
      <section class="col-left">
        <div class="left-stack">
          <div class="upload-block">
            <SectionPanel :title="$t('分子输入')">
              <el-tabs v-model="activeTab">
                <el-tab-pane :label="$t('配体')" name="ligand">
                  <el-tabs v-model="ligandMode" size="small">
                    <el-tab-pane :label="$t('上传配体文件')" name="upload">
                      <FileUpload
                        ref="ligandUpload"
                        :accept="LIGAND_ACCEPT"
                        :extensions="LIGAND_EXTENSIONS"
                        :hint="$t('上传 cdxml / sdf / mol / mol2 / smi 配体文件')"
                        @change="onLigandFile"
                        @clear="clearLigand"
                      />
                    </el-tab-pane>
                    <el-tab-pane label="SMILES" name="smiles">
                      <el-input
                        v-model="smiles"
                        type="textarea"
                        :rows="3"
                        :placeholder="$t('例如：CCO（乙醇）')"
                      />
                      <el-button
                        class="smiles-btn"
                        type="primary"
                        plain
                        :loading="preparing"
                        @click="generateFromSmiles"
                      >
                        {{ $t('生成配体') }}
                      </el-button>
                    </el-tab-pane>
                  </el-tabs>
                </el-tab-pane>
                <el-tab-pane :label="$t('受体')" name="receptor">
                  <div class="pdb-row">
                    <el-input
                      v-model="pdbId"
                      :placeholder="$t('例如 1CRN')"
                      @keyup.enter="fetchPdb"
                    />
                    <el-button :loading="preparing" @click="fetchPdb">{{ $t('拉取 PDB') }}</el-button>
                  </div>
                  <el-divider content-position="center">{{ $t('或') }}</el-divider>
                  <FileUpload
                    ref="receptorUpload"
                    :accept="RECEPTOR_ACCEPT"
                    :extensions="RECEPTOR_EXTENSIONS"
                    :hint="$t('上传本地受体 PDB / PDBQT 文件')"
                    @change="onReceptorFile"
                    @clear="clearReceptor"
                  />
                </el-tab-pane>
              </el-tabs>

              <div v-if="ligandInfo" class="ligand-meta">
                <div>SMILES：<span class="mono">{{ ligandInfo.smiles || '-' }}</span></div>
                <div>
                  {{ $t('属性：MW {weight}，可旋转键 {bonds}', {
                    weight: ligandInfo.properties?.molecular_weight ?? '-',
                    bonds: ligandInfo.properties?.rotatable_bonds ?? '-'
                  }) }}
                </div>
              </div>
            </SectionPanel>
          </div>

          <div class="box-block">
            <SectionPanel :title="$t('对接盒子与计算参数')">
              <el-form label-width="118px">
                <EngineSelect v-model="dock.params.engine_id" :engines="settings.engines" />
              </el-form>
              <BoxConfigPanel
                v-model="dock.params"
                v-model:box-mode="dock.boxMode"
                :can-use-centroid="Boolean(ligandInfo?.centroid)"
                :can-auto-pocket="Boolean(ligandInfo?.pdbqt_path && receptorInfo?.pdbqt)"
                :auto-pocket-loading="autoPocketLoading"
                @use-centroid="applyCentroid"
                @auto-pocket="predictPocket"
              />
              <EngineParamsPanel v-model="dock.params" />

              <div class="box-canvas-wrap">
                <div class="box-canvas-title muted">{{ $t('对接盒子三维线框（仅本区域渲染）') }}</div>
                <MoleculeViewer3D :files="[]" :box="box3d" height="260px" :interactive="false" />
              </div>
            </SectionPanel>
          </div>
        </div>
      </section>

      <!-- 右栏：分子合并预览 -->
      <section class="col-right">
        <SectionPanel :title="$t('蛋白 + 配体合并预览')">
          <div class="preview-guide muted">
            {{ $t('可拖拽立方体调整对接盒子，或点击左侧自动生成口袋快速获取最优结合位点') }}
          </div>
          <MoleculeViewer3D
            :files="mergeFiles"
            :box="box3d"
            height="560px"
            :interactive="true"
            @box-change="onCanvasBoxChange"
          />
          <el-alert
            v-if="!mergeReady"
            :title="$t('请先在左侧完成配体与受体输入')"
            type="info"
            :closable="false"
            show-icon
            class="merge-alert"
          />
          <div class="box-summary muted">
            {{ $t('盒子中心 ({x}, {y}, {z})', {
              x: box3d.center.x,
              y: box3d.center.y,
              z: box3d.center.z
            }) }}，
            {{ $t('尺寸 ({x}, {y}, {z})', {
              x: box3d.size.x,
              y: box3d.size.y,
              z: box3d.size.z
            }) }} Å
          </div>
        </SectionPanel>
      </section>
    </div>

    <!-- 底部全局操作区 -->
    <div class="action-bar">
      <div v-if="taskId" class="task-progress">
        <el-progress
          :percentage="progress"
          :status="status === 'failed' ? 'exception' : undefined"
          style="width: 260px"
        />
        <span class="muted">{{ statusLabel }}</span>
      </div>
      <div class="action-buttons">
        <el-button type="primary" :loading="submitting" @click="submitTask">{{ $t('提交任务') }}</el-button>
        <el-button @click="resetAll">{{ $t('重置参数') }}</el-button>
        <el-button @click="templateDialog = true">{{ $t('保存参数模板') }}</el-button>
      </div>
    </div>

    <el-dialog v-model="templateDialog" :title="$t('保存参数模板')" width="420px">
      <el-form label-width="80px">
        <el-form-item :label="$t('模板名称')" required>
          <el-input v-model="templateName" :placeholder="$t('例如：激酶口袋-默认盒子')" />
        </el-form-item>
        <div class="muted">{{ $t('将保存当前引擎、盒子与计算参数，便于后续复用。') }}</div>
      </el-form>
      <template #footer>
        <el-button @click="templateDialog = false">{{ $t('取消') }}</el-button>
        <el-button type="primary" :loading="savingTemplate" @click="saveTemplate">{{ $t('保存') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import SectionPanel from '../components/common/SectionPanel.vue'
import FileUpload from '../components/common/FileUpload.vue'
import EngineSelect from '../components/config/EngineSelect.vue'
import BoxConfigPanel from '../components/config/BoxConfigPanel.vue'
import EngineParamsPanel from '../components/config/EngineParamsPanel.vue'
import MoleculeViewer3D from '../components/molecule/MoleculeViewer3D.vue'
import { useDockStore } from '../stores/dock'
import { useSettingsStore } from '../stores/settings'
import { createTask } from '../api/task'
import { autoPocket, runDocking } from '../api/docking'
import { prepareLigand, prepareReceptorFile, prepareReceptorPdbId, prepareSmiles, previewUrl } from '../api/molecule'
import { saveTemplate as saveTemplateApi } from '../api/system'
import { useTaskPolling } from '../composables/useTaskPolling'
import {
  LIGAND_ACCEPT,
  LIGAND_EXTENSIONS,
  RECEPTOR_ACCEPT,
  RECEPTOR_EXTENSIONS
} from '../utils/constants'
import { translateBackendMessage } from '../utils/backendMessages'
import { validateBox, validatePdbId, validateSmiles } from '../utils/validators'

const router = useRouter()
const settings = useSettingsStore()
const { t } = useI18n()

const activeTab = ref('ligand')
const ligandMode = ref('upload')
const smiles = ref('')
const pdbId = ref('')
const preparing = ref(false)
const submitting = ref(false)
const savingTemplate = ref(false)
const templateDialog = ref(false)
const templateName = ref('')
const autoPocketLoading = ref(false)
const ligandUpload = ref(null)
const receptorUpload = ref(null)

const ligandInfo = ref(null)
const receptorInfo = ref(null)
const receptorLabel = ref('')
const ligandLabel = ref('')

const dock = useDockStore()

const taskId = ref('')
const { status, progress, statusLabel, start, stop } = useTaskPolling(taskId)

const mergeFiles = computed(() => {
  const files = []
  if (receptorInfo.value?.pdbqt) {
    files.push({ url: previewUrl(receptorInfo.value.pdbqt), style: 'protein', label: 'receptor' })
  }
  if (ligandInfo.value?.pdbqt_path) {
    files.push({ url: previewUrl(ligandInfo.value.pdbqt_path), style: 'ligand', label: 'ligand' })
  }
  return files
})

const box3d = computed(() => ({
  center: { x: dock.params.center_x, y: dock.params.center_y, z: dock.params.center_z },
  size: { x: dock.params.size_x, y: dock.params.size_y, z: dock.params.size_z }
}))

const mergeReady = computed(() => Boolean(ligandInfo.value && receptorInfo.value))

onMounted(async () => {
  await settings.loadEngines()
  if (settings.loadedParams) {
    dock.applyLoadedParams(settings.loadedParams)
    settings.loadedParams = null
    ElMessage.success(t('已加载参数模板'))
  }
})

function setLigandFromResponse(result, label) {
  const ligand = result.ligands?.[0]
  if (!ligand) return
  ligandInfo.value = ligand
  ligandLabel.value = label || ligand.name
  if (ligand.centroid) {
    dock.setCenter(ligand.centroid)
  }
  const warnings = [...(result.warnings || []), ...(ligand.warnings || [])]
  if (warnings.length) {
    ElMessage.warning(translateBackendMessage(warnings[0]))
  }
  activeTab.value = 'ligand'
}

async function onLigandFile(file) {
  preparing.value = true
  try {
    const result = await prepareLigand(file)
    setLigandFromResponse(result, file.name)
  } catch {
    ligandUpload.value?.clear()
  } finally {
    preparing.value = false
  }
}

async function generateFromSmiles() {
  if (!validateSmiles(smiles.value)) return
  preparing.value = true
  try {
    const result = await prepareSmiles(smiles.value.trim())
    setLigandFromResponse(result, `${smiles.value.trim()} (SMILES)`)
  } finally {
    preparing.value = false
  }
}

async function onReceptorFile(file) {
  preparing.value = true
  try {
    const result = await prepareReceptorFile(file)
    applyReceptor(result, file.name)
  } catch {
    receptorUpload.value?.clear()
  } finally {
    preparing.value = false
  }
}

async function fetchPdb() {
  if (!validatePdbId(pdbId.value)) return
  preparing.value = true
  try {
    const result = await prepareReceptorPdbId(pdbId.value.trim())
    applyReceptor(result, pdbId.value.trim())
  } finally {
    preparing.value = false
  }
}

function applyReceptor(result, label) {
  if (!result.receptor) return
  receptorInfo.value = result.receptor
  receptorLabel.value = label
  activeTab.value = 'receptor'
}

function clearLigand() {
  ligandInfo.value = null
  ligandLabel.value = ''
}

function clearReceptor() {
  receptorInfo.value = null
  receptorLabel.value = ''
}

function applyCentroid() {
  if (!ligandInfo.value?.centroid) return
  dock.setCenter(ligandInfo.value.centroid)
    ElMessage.success(t('盒子中心已设为配体质心'))
}

function onCanvasBoxChange({ center, size }) {
  dock.setBox({
    center: {
      x: Number(center.x.toFixed(2)),
      y: Number(center.y.toFixed(2)),
      z: Number(center.z.toFixed(2))
    },
    size: {
      x: Number(size.x.toFixed(2)),
      y: Number(size.y.toFixed(2)),
      z: Number(size.z.toFixed(2))
    }
  })
}

async function predictPocket() {
  if (!ligandInfo.value?.pdbqt_path || !receptorInfo.value?.pdbqt) {
    ElMessage.warning(t('请先完成配体与受体输入'))
    return
  }
  autoPocketLoading.value = true
  try {
    const box = await autoPocket({
      receptor_path: receptorInfo.value.pdbqt,
      ligand_path: ligandInfo.value.pdbqt_path,
      padding: 6
    })
    dock.applyPocket(box)
    const methodLabel = {
      fpocket: t('FPocket 口袋扫描'),
      geometry_cavity: t('蛋白空腔识别'),
      protein_center: t('蛋白几何中心兜底')
    }[box.method] || t('口袋预测')
    if (box.method === 'protein_center') {
      ElMessage.warning(t('未识别明显结合口袋，已加载蛋白中心默认盒子，可手动拖拽调整'))
    } else if (box.warnings?.length) {
      const warning = translateBackendMessage(box.warnings[0])
      ElMessage.warning(t('口袋盒子已生成（{method}）：{warning}', {
        method: methodLabel,
        warning
      }))
    } else {
      ElMessage.success(t('口袋盒子已生成', { method: methodLabel }))
    }
  } catch {
    // 统一错误提示已由 http 拦截器处理
  } finally {
    autoPocketLoading.value = false
  }
}

function resetAll() {
  dock.reset()
  ligandInfo.value = null
  receptorInfo.value = null
  ligandLabel.value = ''
  receptorLabel.value = ''
  smiles.value = ''
  pdbId.value = ''
  autoPocketLoading.value = false
  taskId.value = ''
  ligandUpload.value?.clear()
  receptorUpload.value?.clear()
  stop()
}

async function submitTask() {
  if (!ligandInfo.value?.pdbqt_path) {
    ElMessage.warning(t('请先上传配体文件或输入 SMILES 生成配体'))
    return
  }
  if (!receptorInfo.value?.pdbqt) {
    ElMessage.warning(t('请先输入 PDB ID 或上传受体 PDB 文件'))
    return
  }
  if (!validateBox(dock.params)) return

  const taskName = `${ligandLabel.value || 'ligand'}__${receptorLabel.value || 'receptor'}`
  const fileParams = {
    ...dock.params,
    pdb_id: pdbId.value.trim(),
    receptor_path: receptorInfo.value.pdbqt,
    ligand_path: ligandInfo.value.pdbqt_path
  }

  submitting.value = true
  try {
    const task = await createTask({
      name: taskName,
      engine_id: dock.params.engine_id,
      params: fileParams
    })
    taskId.value = task.task_id
    start()
    await runDocking({
      task_id: task.task_id,
      engine_id: dock.params.engine_id,
      receptor_path: receptorInfo.value.pdbqt,
      ligand_path: ligandInfo.value.pdbqt_path,
      center_x: dock.params.center_x,
      center_y: dock.params.center_y,
      center_z: dock.params.center_z,
      size_x: dock.params.size_x,
      size_y: dock.params.size_y,
      size_z: dock.params.size_z,
      exhaustiveness: dock.params.exhaustiveness,
      energy_range: dock.params.energy_range,
      num_modes: dock.params.num_modes,
      seed: dock.params.seed,
      cpu: dock.params.cpu,
      timeout_seconds: dock.params.timeout_seconds
    })
    stop()
    router.push(`/result/${task.task_id}`)
  } catch {
    stop()
  } finally {
    submitting.value = false
  }
}

async function saveTemplate() {
  if (!templateName.value.trim()) {
    ElMessage.warning(t('请输入模板名称'))
    return
  }
  savingTemplate.value = true
  try {
    await saveTemplateApi({ name: templateName.value.trim(), params: { ...dock.params } })
    templateDialog.value = false
    templateName.value = ''
    ElMessage.success(t('参数模板已保存'))
  } finally {
    savingTemplate.value = false
  }
}
</script>

<style scoped>
.home-grid {
  display: grid;
  grid-template-columns: minmax(430px, 520px) 1fr;
  gap: 14px;
  align-items: start;
}

.col-left,
.col-right {
  min-width: 0;
}

/* 左栏垂直分区：上传区置顶，盒子画布区隔离在下方 */
.left-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.upload-block {
  position: relative;
  z-index: 10;
  background: var(--cadd-panel);
}

.box-block {
  position: relative;
  z-index: 0;
  margin-top: 18px;
  overflow: hidden;
}

/* 画布固定上外边距，与上传区域强制留白分隔 */
.box-canvas-wrap {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed rgba(96, 165, 250, 0.22);
  overflow: hidden;
}

.box-canvas-title {
  margin-bottom: 8px;
  font-size: 12px;
}

.smiles-btn {
  width: 100%;
  margin-top: 8px;
}

.pdb-row {
  display: flex;
  gap: 8px;
}

.ligand-meta {
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--cadd-muted);
}

.merge-alert {
  margin-top: 10px;
}

.preview-guide {
  margin-bottom: 8px;
  font-size: 12px;
  line-height: 1.6;
  opacity: 0.6;
  transition: opacity 0.25s ease-out;
}

.preview-guide:hover {
  opacity: 1;
}

.box-summary {
  margin-top: 10px;
  font-size: 12px;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
  padding: 14px 18px;
  background: rgba(17, 25, 43, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--cadd-radius-card);
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
}

.col-right :deep(.section-panel) {
  border-color: rgba(96, 165, 250, 0.18);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 20px 46px rgba(0, 0, 0, 0.28);
}

.col-right :deep(.viewer3d) {
  border-color: rgba(96, 165, 250, 0.22);
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

@media (max-width: 1100px) {
  .home-grid {
    grid-template-columns: 1fr;
  }
}
</style>
