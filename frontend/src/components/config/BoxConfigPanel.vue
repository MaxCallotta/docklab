<template>
  <div class="box-config-panel">
    <div class="box-mode-row">
      <el-radio-group v-model="boxMode" class="box-mode-switch">
        <el-radio-button :value="BOX_MODE.MANUAL">{{ $t('手动自定义盒子') }}</el-radio-button>
        <el-radio-button :value="BOX_MODE.AUTO">{{ $t('自动预测口袋盒子') }}</el-radio-button>
      </el-radio-group>
    </div>

    <div class="auto-pocket-row">
      <el-button
        type="primary"
        plain
        size="default"
        :loading="autoPocketLoading"
        :disabled="!canAutoPocket"
        @click="$emit('auto-pocket')"
      >
        {{ $t('一键计算最优口袋盒子') }}
      </el-button>
      <span v-if="!canAutoPocket" class="muted auto-pocket-hint">{{ $t('需先完成配体与受体输入') }}</span>
    </div>

    <el-form label-width="86px" size="default">
      <el-form-item :label="$t('盒子中心')">
        <div class="box-grid">
          <el-input-number v-model="params.center_x" :min="-2000" :max="2000" :precision="2" :step="1" />
          <el-input-number v-model="params.center_y" :min="-2000" :max="2000" :precision="2" :step="1" />
          <el-input-number v-model="params.center_z" :min="-2000" :max="2000" :precision="2" :step="1" />
        </div>
      </el-form-item>
      <el-form-item :label="$t('盒子尺寸')">
        <div class="box-grid">
          <el-input-number v-model="params.size_x" :min="1" :max="200" :precision="2" :step="1" />
          <el-input-number v-model="params.size_y" :min="1" :max="200" :precision="2" :step="1" />
          <el-input-number v-model="params.size_z" :min="1" :max="200" :precision="2" :step="1" />
        </div>
      </el-form-item>
      <el-form-item>
        <el-button size="small" :disabled="!canUseCentroid" @click="$emit('use-centroid')">
          {{ $t('以配体质心填充') }}
        </el-button>
        <span class="muted box-note">{{ $t('单位：埃（Å）') }}</span>
      </el-form-item>
    </el-form>

    <div class="muted box-guide">
      {{ $t('提示：右侧画布中拖拽盒体移动中心，拖拽顶点调整尺寸，滚轮缩放场景；中心范围 ±2000 Å，尺寸范围 1–200 Å。') }}
    </div>
  </div>
</template>

<script setup>
import { BOX_MODE } from '../../utils/constants'

defineProps({
  canUseCentroid: { type: Boolean, default: false },
  canAutoPocket: { type: Boolean, default: false },
  autoPocketLoading: { type: Boolean, default: false }
})

defineEmits(['use-centroid', 'auto-pocket'])

// 直接绑定父级 params 对象，保持单一数据源
const params = defineModel({ type: Object, required: true })
const boxMode = defineModel('boxMode', { type: String, default: BOX_MODE.MANUAL })
</script>

<style scoped>
.box-config-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.box-mode-row {
  display: flex;
  justify-content: center;
}

.box-mode-switch {
  width: 100%;
}

.box-mode-switch :deep(.el-radio-button) {
  flex: 1;
}

.box-mode-switch :deep(.el-radio-button__inner) {
  width: 100%;
}

.auto-pocket-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.auto-pocket-hint {
  font-size: 12px;
}

.box-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  width: 100%;
}

.box-note {
  margin-left: 10px;
  font-size: 12px;
}

.box-guide {
  padding-top: 8px;
  border-top: 1px dashed var(--cadd-border);
  font-size: 12px;
  line-height: 1.7;
}
</style>
