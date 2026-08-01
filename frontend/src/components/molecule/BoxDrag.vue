<template>
  <svg
    v-if="interactive && hasBox"
    ref="overlayEl"
    class="box-overlay"
    @wheel.prevent="onOverlayWheel"
    @pointerdown="onOverlayPointerDown"
  >
    <g class="box-edges">
      <line
        v-for="([a, b], edgeIndex) in EDGE_PAIRS"
        :key="`edge-${edgeIndex}`"
        class="box-edge"
        :x1="screenPoints[a]?.x"
        :y1="screenPoints[a]?.y"
        :x2="screenPoints[b]?.x"
        :y2="screenPoints[b]?.y"
      />
    </g>
    <polygon class="box-body" :points="bodyPoints" />
    <g class="box-handles">
      <circle
        v-for="(point, index) in screenPoints"
        :key="`handle-${index}`"
        class="box-handle"
        :cx="point.x"
        :cy="point.y"
        r="7"
        :data-index="index"
        @pointerdown.stop="onHandlePointerDown($event, index)"
      />
    </g>
  </svg>

  <div
    v-if="dragHintVisible"
    class="drag-hint"
    :style="{ left: `${hintX}px`, top: `${hintY}px` }"
  >
    {{ dragHintText }}
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  box: { type: Object, default: null },
  projector: { type: Object, default: null },
  interactive: { type: Boolean, default: true }
})

const emit = defineEmits(['box-change', 'drag-start', 'drag-end'])
const { t } = useI18n()

const CENTER_MIN = -2000
const CENTER_MAX = 2000
const SIZE_MIN = 1
const SIZE_MAX = 200

const EDGE_PAIRS = [
  [0, 1], [1, 2], [2, 3], [3, 0],
  [4, 5], [5, 6], [6, 7], [7, 4],
  [0, 4], [1, 5], [2, 6], [3, 7]
]

const overlayEl = ref(null)
const screenPoints = ref([])
const bodyPoints = ref('')
const dragHintVisible = ref(false)
const dragHintText = ref('')
const hintX = ref(0)
const hintY = ref(0)

let dragState = null
let pendingBox = null
let rafId = 0
let clampedWarned = false

const hasBox = computed(() => Boolean(props.box && props.box.size))

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

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

function convexHull(points) {
  if (points.length < 3) return points
  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y)
  const cross = (o, a, b) =>
    (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
  const lower = []
  for (const point of sorted) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], point) <= 0) {
      lower.pop()
    }
    lower.push(point)
  }
  const upper = []
  for (let index = sorted.length - 1; index >= 0; index -= 1) {
    const point = sorted[index]
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], point) <= 0) {
      upper.pop()
    }
    upper.push(point)
  }
  lower.pop()
  upper.pop()
  return lower.concat(upper)
}

function refresh() {
  if (!props.projector || !hasBox.value || !overlayEl.value) return
  const box = normalizeBox(props.box)
  const corners = boxCorners(box)
  let projected
  try {
    projected = props.projector.toScreen(corners)
  } catch {
    return
  }
  const rect = overlayEl.value.getBoundingClientRect()
  const offsetX = rect.left + window.scrollX
  const offsetY = rect.top + window.scrollY
  const points = projected.map((point) => ({
    x: point.x - offsetX,
    y: point.y - offsetY
  }))
  if (points.some((point) => !Number.isFinite(point.x) || !Number.isFinite(point.y))) {
    return
  }
  screenPoints.value = points
  bodyPoints.value = convexHull(points)
    .map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`)
    .join(' ')
}

function updateHint(event) {
  if (!overlayEl.value) return
  const rect = overlayEl.value.getBoundingClientRect()
  hintX.value = clamp(event.clientX - rect.left + 14, 8, Math.max(8, rect.width - 230))
  hintY.value = clamp(event.clientY - rect.top + 14, 8, Math.max(8, rect.height - 42))
}

function warnClamped() {
  if (clampedWarned) return
  clampedWarned = true
  ElMessage.warning(t('拖拽已自动限制在合理范围：中心 ±2000 Å，尺寸 1–200 Å'))
}

function emitThrottled(box) {
  pendingBox = box
  if (rafId) return
  rafId = requestAnimationFrame(() => {
    rafId = 0
    if (pendingBox) {
      emit('box-change', pendingBox)
      pendingBox = null
    }
  })
}

function beginDrag(type, event, index) {
  if (!props.projector || !props.interactive) return
  const box = normalizeBox(props.box)
  const corner = type === 'vertex' ? boxCorners(box)[index] : null
  dragState = {
    type,
    index,
    startX: event.clientX,
    startY: event.clientY,
    startCenter: { ...box.center },
    startSize: { ...box.size },
    startCorner: corner
  }
  clampedWarned = false
  dragHintVisible.value = true
  dragHintText.value = type === 'vertex' ? t('拖拽顶点调整盒子尺寸') : t('拖拽盒体移动中心')
  updateHint(event)
  emit('drag-start')
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', endDrag)
  window.addEventListener('pointercancel', endDrag)
}

function onPointerMove(event) {
  if (!dragState || !props.projector) return
  updateHint(event)
  const dx = event.clientX - dragState.startX
  const dy = event.clientY - dragState.startY

  if (dragState.type === 'body') {
    const delta = props.projector.screenOffsetToModel(dx, dy, dragState.startCenter.z)
    const raw = {
      x: dragState.startCenter.x + delta.x,
      y: dragState.startCenter.y + delta.y,
      z: dragState.startCenter.z + delta.z
    }
    if (Object.values(raw).some((value) => value < CENTER_MIN || value > CENTER_MAX)) {
      warnClamped()
    }
    emitThrottled({
      center: {
        x: clamp(raw.x, CENTER_MIN, CENTER_MAX),
        y: clamp(raw.y, CENTER_MIN, CENTER_MAX),
        z: clamp(raw.z, CENTER_MIN, CENTER_MAX)
      },
      size: { ...dragState.startSize },
      source: 'canvas-body'
    })
    return
  }

  const delta = props.projector.screenOffsetToModel(dx, dy, dragState.startCorner.z)
  let bestAxis = 'x'
  let bestMagnitude = -1
  ;['x', 'y', 'z'].forEach((axis) => {
    const magnitude = Math.abs(delta[axis])
    if (magnitude > bestMagnitude) {
      bestMagnitude = magnitude
      bestAxis = axis
    }
  })
  const sign =
    Math.sign(dragState.startCorner[bestAxis] - dragState.startCenter[bestAxis]) || 1
  const rawSize = dragState.startSize[bestAxis] + 2 * sign * delta[bestAxis]
  if (rawSize < SIZE_MIN || rawSize > SIZE_MAX) {
    warnClamped()
  }
  const size = { ...dragState.startSize }
  size[bestAxis] = clamp(rawSize, SIZE_MIN, SIZE_MAX)
  emitThrottled({
    center: { ...dragState.startCenter },
    size,
    source: 'canvas-vertex'
  })
}

function endDrag() {
  if (rafId) {
    cancelAnimationFrame(rafId)
    rafId = 0
  }
  if (pendingBox) {
    emit('box-change', pendingBox)
    pendingBox = null
  }
  dragState = null
  dragHintVisible.value = false
  emit('drag-end')
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', endDrag)
  window.removeEventListener('pointercancel', endDrag)
}

function onOverlayPointerDown(event) {
  if (!props.interactive || event.button !== 0) return
  if (!event.target.classList || !event.target.classList.contains('box-body')) return
  event.preventDefault()
  beginDrag('body', event, -1)
}

function onHandlePointerDown(event, index) {
  if (!props.interactive || event.button !== 0) return
  event.preventDefault()
  beginDrag('vertex', event, index)
}

function onOverlayWheel(event) {
  if (!props.projector || !props.interactive) return
  const factor = event.deltaY > 0 ? 1.12 : 0.9
  props.projector.zoom(factor)
}

watch(
  () => props.box,
  () => refresh(),
  { deep: true }
)

defineExpose({ refresh })
</script>

<style scoped>
.box-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}

.box-body {
  fill: rgba(64, 158, 255, 0.08);
  stroke: rgba(37, 99, 235, 0.9);
  stroke-width: 1.5;
  pointer-events: auto;
  cursor: grab;
  transition: fill 0.15s ease;
}

.box-body:hover {
  fill: rgba(64, 158, 255, 0.18);
}

.box-body:active {
  cursor: grabbing;
}

.box-edge {
  stroke: rgba(37, 99, 235, 0.85);
  stroke-width: 1.5;
  pointer-events: none;
}

.box-handle {
  fill: #f97316;
  stroke: #ffffff;
  stroke-width: 2;
  pointer-events: auto;
  cursor: grab;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.35));
  transition: r 0.12s ease, fill 0.12s ease;
}

.box-handle:hover {
  fill: #fb923c;
  r: 8.5;
}

.box-handle:active {
  cursor: grabbing;
  fill: #ea580c;
}

.drag-hint {
  position: absolute;
  z-index: 3;
  padding: 5px 10px;
  border-radius: 6px;
  background: rgba(17, 24, 39, 0.82);
  color: #ffffff;
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
  pointer-events: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
</style>
