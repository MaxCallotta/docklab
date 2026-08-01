<template>
  <div class="export-actions">
    <el-select v-model="format" style="width: 120px">
      <el-option v-for="item in POSE_FORMATS" :key="item.value" :value="item.value" :label="item.label" />
    </el-select>
    <el-button type="primary" :disabled="disabled" @click="$emit('export-pose', format)">
      <el-icon><Download /></el-icon>
      {{ $t('导出选中构象') }}
    </el-button>
    <el-button :disabled="disabled" @click="$emit('generate-pml')">
      <el-icon><MagicStick /></el-icon>
      {{ $t('生成 PML 脚本') }}
    </el-button>
    <el-button :disabled="disabled" @click="$emit('open-pymol')">
      <el-icon><Monitor /></el-icon>
      {{ $t('唤起本地 PyMOL') }}
    </el-button>
    <el-button :disabled="disabled" @click="$emit('export-csv')">
      <el-icon><Document /></el-icon>
      {{ $t('导出打分 CSV') }}
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Document, Download, MagicStick, Monitor } from '@element-plus/icons-vue'
import { POSE_FORMATS } from '../../utils/constants'

defineProps({
  disabled: { type: Boolean, default: false }
})

defineEmits(['export-pose', 'generate-pml', 'open-pymol', 'export-csv'])

const format = ref('pdbqt')
</script>

<style scoped>
.export-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
</style>
