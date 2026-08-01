<template>
  <el-table
    :data="poses"
    :default-sort="{ prop: 'affinity', order: 'ascending' }"
    highlight-current-row
    :row-class-name="rowClassName"
    @row-click="handleRowClick"
    :empty-text="$t('暂无打分数据')"
    size="default"
  >
    <el-table-column :label="$t('最优')" width="70" align="center">
      <template #default="{ row }">
        <el-radio
          :model-value="currentIndex"
          :label="row.index"
          @change="selectPose(row.index)"
        />
      </template>
    </el-table-column>
    <el-table-column prop="index" :label="$t('构象')" width="80" sortable align="center" />
    <el-table-column
      prop="affinity"
      :label="$t('结合自由能 (kcal/mol)')"
      width="180"
      sortable
      align="right"
    >
      <template #default="{ row }">
        <span :class="{ 'best-score': row.index === currentIndex }">
          {{ row.affinity?.toFixed ? row.affinity.toFixed(2) : row.affinity }}
        </span>
      </template>
    </el-table-column>
    <el-table-column prop="rmsd_lb" label="RMSD L.B." width="120" sortable align="right" />
    <el-table-column prop="rmsd_ub" label="RMSD U.B." width="120" sortable align="right" />
  </el-table>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  poses: { type: Array, default: () => [] },
  modelValue: { type: Number, default: 1 }
})

const emit = defineEmits(['update:modelValue', 'select'])
const currentIndex = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function selectPose(index) {
  currentIndex.value = index
  emit('select', index)
}

function handleRowClick(row) {
  selectPose(row.index)
}

function rowClassName({ row }) {
  return row.index === props.modelValue ? 'current-pose-row' : ''
}
</script>

<style scoped>
.best-score {
  font-weight: 600;
  color: var(--cadd-accent);
}
</style>

<style>
.el-table .current-pose-row {
  background: var(--cadd-accent-soft) !important;
}
</style>
