<template>
  <el-card class="section-panel" shadow="never">
    <template #header>
      <div class="section-header">
        <span class="section-title">{{ title }}</span>
        <slot name="extra" />
      </div>
    </template>
    <div class="section-body">
      <slot />
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' }
})
</script>

<style scoped>
.section-panel {
  margin-bottom: 14px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 8px;
  border-left: 3px solid var(--cadd-accent);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--cadd-ink);
}

.section-body {
  width: 100%;
}
</style>
