<template>
  <div
    ref="container"
    class="viewer3d"
    :class="{ 'is-interactive': interactive && hasBox }"
    :style="{ height }"
  >
    <BoxDrag
      v-if="interactive && hasBox"
      ref="boxDragRef"
      :box="props.box"
      :projector="projector"
      @box-change="onBoxChange"
      @drag-start="onDragStart"
      @drag-end="onDragEnd"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import * as $3Dmol from '3dmol/build/3Dmol.js'

import BoxDrag from './BoxDrag.vue'

const props = defineProps({
  // [{ url, label, style: 'protein' | 'ligand' }]
  files: { type: Array, default: () => [] },
  // { center: {x,y,z}, size: {x,y,z} }
  box: { type: Object, default: null },
  height: { type: String, default: '420px' },
  // 是否启用盒子拖拽交互（非交互预览仍绘制 3D 盒子）
  interactive: { type: Boolean, default: true }
})

const emit = defineEmits(['box-change'])
const { t } = useI18n()

const BOX_COLOR = '#409eff'
const EDGE_COLOR = '#2563eb'

const EDGE_PAIRS = [
  [0, 1], [1, 2], [2, 3], [3, 0],
  [4, 5], [5, 6], [6, 7], [7, 4],
  [0, 4], [1, 5], [2, 6], [3, 7]
]

const container = ref(null)
const boxDragRef = ref(null)
const projector = ref(null)

let viewer = null
let renderSeq = 0
let draggingBox = false
let resizeObserver = null

const hasBox = computed(() => Boolean(props.box && props.box.size))

function normalizeBox(box) {
  const center = box.center || {}
  const size = box.size || {}
  return {
    center: {
      x: Number(center.x) || 0,
      y: Number(center.y) || 0,
      z: Number(center.z) || 0
    },
    size: {
      x: Number(size.x) || 20,
      y: Number(size.y) || 20,
      z: Number(size.z) || 20
    }
  }
}

function boxCorners(box) {
  const { x, y, z } = box.center
  const hx = box.size.x / 2
  const hy = box.size.y / 2
  const hz = box.size.z / 2
  return [
    { x: x - hx, y: y - hy, z: z - hz },
    { x: x + hx, y: y - hy, z: z - hz },
    { x: x + hx, y: y + hy, z: z - hz },
    { x: x - hx, y: y + hy, z: z - hz },
    { x: x - hx, y: y - hy, z: z + hz },
    { x: x + hx, y: y - hy, z: z + hz },
    { x: x + hx, y: y + hy, z: z + hz },
    { x: x - hx, y: y + hy, z: z + hz }
  ]
}

function refreshBoxDrag() {
  boxDragRef.value?.refresh()
}

function updateBoxShapes() {
  if (!viewer || !hasBox.value) return
  const box = normalizeBox(props.box)
  viewer.removeAllShapes()
  viewer.addBox({
    center: box.center,
    dimensions: { w: box.size.x, h: box.size.y, d: box.size.z },
    color: BOX_COLOR,
    opacity: 0.14
  })
  const corners = boxCorners(box)
  EDGE_PAIRS.forEach(([a, b]) => {
    viewer.addLine({
      start: corners[a],
      end: corners[b],
      color: EDGE_COLOR,
      linewidth: 2.5
    })
  })
  viewer.render()
  refreshBoxDrag()
}

function inferFormat(url) {
  const lower = url.toLowerCase()
  if (lower.endsWith('.sdf')) return 'sdf'
  if (lower.endsWith('.mol2')) return 'mol2'
  if (lower.endsWith('.pdbqt')) return 'pdb'
  return 'pdb'
}

function styleFor(kind) {
  if (kind === 'protein') {
    return { cartoon: { color: 'spectrum' } }
  }
  return {
    stick: { radius: 0.2, colorscheme: 'Jmol' },
    sphere: { scale: 0.22, colorscheme: 'Jmol' }
  }
}

async function loadModels() {
  if (!viewer || !container.value) return
  const seq = ++renderSeq
  viewer.removeAllModels()
  viewer.removeAllShapes()
  try {
    let modelIndex = 0
    for (const file of props.files) {
      if (seq !== renderSeq) return
      const response = await fetch(file.url)
      if (!response.ok) throw new Error(t('无法加载结构：{url}', { url: file.url }))
      const text = await response.text()
      if (!text.trim()) continue
      viewer.addModel(text, inferFormat(file.url))
      viewer.setStyle({ model: modelIndex }, styleFor(file.style || 'ligand'))
      modelIndex += 1
    }
    if (props.files.length) {
      try {
        viewer.zoomTo()
      } catch {
        // 空场景时保持默认相机
      }
    }
    updateBoxShapes()
    viewer.render()
    refreshBoxDrag()
  } catch (error) {
    ElMessage.error(error.message || t('预览加载失败'))
  }
}

function onBoxChange(payload) {
  emit('box-change', payload)
}

function onDragStart() {
  draggingBox = true
}

function onDragEnd() {
  draggingBox = false
  updateBoxShapes()
}

watch(
  () => props.files,
  () => loadModels(),
  { deep: true }
)

watch(
  () => props.box,
  () => {
    if (draggingBox) {
      // 拖拽中仅由 BoxDrag 刷新投影覆盖层，避免高频重绘 3D 场景
      refreshBoxDrag()
      return
    }
    updateBoxShapes()
  },
  { deep: true }
)

onMounted(() => {
  viewer = $3Dmol.createViewer(container.value, {
    backgroundColor: 'white',
    antialias: true
  })
  projector.value = {
    toScreen: (coords) => viewer.modelToScreen(coords),
    screenOffsetToModel: (dx, dy, modelZ) => viewer.screenOffsetToModel(dx, dy, modelZ),
    zoom: (factor) => viewer.zoom(factor)
  }
  viewer.setViewChangeCallback(() => refreshBoxDrag())
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      if (!viewer) return
      viewer.resize()
      refreshBoxDrag()
    })
    resizeObserver.observe(container.value)
  }
  window.addEventListener('scroll', refreshBoxDrag, { passive: true })
  loadModels()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', refreshBoxDrag)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (viewer) {
    viewer.clear()
    viewer = null
  }
})

defineExpose({ render: loadModels })
</script>

<style scoped>
.viewer3d {
  position: relative;
  z-index: 0;
  width: 100%;
  border: 1px solid var(--cadd-border);
  border-radius: var(--cadd-radius);
  background: #ffffff;
  overflow: hidden;
}
</style>
