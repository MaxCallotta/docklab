<template>
  <el-form-item label="对接引擎" required>
    <el-select v-model="engineId" placeholder="选择对接软件" style="width: 100%">
      <el-option
        v-for="engine in engines"
        :key="engine.engine_id"
        :value="engine.engine_id"
        :label="engine.engine_name"
        :disabled="!engine.available"
      >
        <span>{{ engine.engine_name }}</span>
        <el-tag
          size="small"
          :type="engine.available ? 'success' : 'info'"
          effect="plain"
          style="margin-left: 8px"
        >
          {{ engine.available ? '可用' : '未配置' }}
        </el-tag>
      </el-option>
    </el-select>
    <div class="muted engine-hint">预留 Glide / MOE / LeDock / rDock 扩展</div>
  </el-form-item>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: 'vina' },
  engines: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue'])
const engineId = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})
</script>

<style scoped>
.engine-hint {
  margin-top: 4px;
  font-size: 12px;
}
</style>
