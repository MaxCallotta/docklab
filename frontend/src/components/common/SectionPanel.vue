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
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 10px;
}

.section-header::before {
  content: "";
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  border-radius: 3px;
  background: linear-gradient(180deg, #3B82F6, #60A5FA);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.35);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--cadd-ink);
  letter-spacing: 0.2px;
}

.section-body {
  width: 100%;
}
</style>
