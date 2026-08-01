<template>
  <div class="preprocess-output">
    <el-form label-width="86px">
      <el-form-item :label="$t('输出格式')">
        <el-select v-model="outputFormat" style="width: 100%">
          <el-option
            v-for="item in PREPROCESS_OUTPUT_FORMATS"
            :key="item.value"
            :value="item.value"
            :label="item.label"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <el-button type="primary" :loading="loading" :disabled="disabled" @click="$emit('run')">
      {{ $t('开始处理') }}
    </el-button>
    <div class="local-note muted">{{ $t('所有处理均在本地完成，数据不会上传') }}</div>
  </div>
</template>

<script setup>
import { PREPROCESS_OUTPUT_FORMATS } from '../../utils/constants'

defineProps({
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: true }
})

defineEmits(['run'])

const outputFormat = defineModel('outputFormat', { type: String, default: 'sdf' })
</script>

<style scoped>
.preprocess-output {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.local-note {
  font-size: 12px;
}
</style>
