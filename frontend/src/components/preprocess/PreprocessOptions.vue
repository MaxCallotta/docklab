<template>
  <div class="preprocess-options">
    <div class="option-group">
      <div class="group-title">{{ $t('结构标准化') }}</div>
      <div class="option-row">
        <el-checkbox v-model="model.add_hydrogens">{{ $t('加氢') }}</el-checkbox>
        <el-checkbox v-model="model.compute_gasteiger">{{ $t('计算Gasteiger电荷') }}</el-checkbox>
        <el-checkbox v-model="model.remove_salts">{{ $t('去盐') }}</el-checkbox>
        <el-checkbox v-model="model.remove_duplicates">{{ $t('去重复分子') }}</el-checkbox>
      </div>
    </div>

    <div class="option-group">
      <div class="group-title">{{ $t('构象生成') }}</div>
      <div class="option-row">
        <el-switch v-model="model.enable_conformations" />
        <span class="option-label">{{ $t('启用构象生成') }}</span>
        <el-input-number
          v-if="model.enable_conformations"
          v-model="model.num_conformations"
          :min="1"
          :max="50"
          :step="1"
          style="width: 110px"
        />
      </div>
    </div>

    <div class="option-group">
      <div class="group-title">{{ $t('属性计算') }}</div>
      <div class="option-row">
        <el-checkbox v-model="model.compute_properties">{{ $t('计算基础理化属性') }}</el-checkbox>
      </div>
    </div>
  </div>
</template>

<script setup>
const model = defineModel({ type: Object, required: true })
</script>

<style scoped>
.preprocess-options {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--cadd-muted);
}

.option-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.option-label {
  font-size: 13px;
  color: var(--cadd-ink);
}
</style>
