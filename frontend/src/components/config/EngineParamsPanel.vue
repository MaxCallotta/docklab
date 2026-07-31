<template>
  <el-form label-width="118px">
    <el-form-item label="Exhaustiveness">
      <div class="param-row">
        <el-slider v-model="params.exhaustiveness" :min="1" :max="64" :step="1" />
        <el-input-number v-model="params.exhaustiveness" :min="1" :max="64" style="width: 110px" />
      </div>
    </el-form-item>
    <el-form-item label="能量窗口">
      <div class="param-row">
        <el-slider v-model="params.energy_range" :min="0.5" :max="5" :step="0.1" />
        <el-input-number
          v-model="params.energy_range"
          :min="0.5"
          :max="5"
          :precision="1"
          :step="0.1"
          style="width: 110px"
        />
      </div>
    </el-form-item>
    <el-form-item label="输出构象数">
      <div class="param-row">
        <el-slider v-model="params.num_modes" :min="1" :max="50" :step="1" />
        <el-input-number v-model="params.num_modes" :min="1" :max="50" style="width: 110px" />
      </div>
    </el-form-item>
    <el-form-item label="随机种子">
      <el-input-number
        v-model="params.seed"
        :min="0"
        :max="2147483647"
        controls-position="right"
        placeholder="留空则随机"
        style="width: 100%"
      />
    </el-form-item>
    <el-form-item label="CPU 核数">
      <el-input-number
        v-model="params.cpu"
        :min="1"
        :max="128"
        controls-position="right"
        placeholder="留空自动"
        style="width: 100%"
      />
    </el-form-item>
    <el-form-item label="超时秒数">
      <el-input-number v-model="params.timeout_seconds" :min="60" :max="86400" :step="60" style="width: 100%" />
    </el-form-item>
  </el-form>
</template>

<script setup>
const params = defineModel({ type: Object, required: true })
</script>

<style scoped>
.param-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.param-row .el-slider {
  flex: 1;
}
</style>
