import { computed, onUnmounted, ref } from 'vue'
import { getTask } from '../api/task'
import { STATUS_MAP } from '../utils/constants'
import i18n from '../i18n'

// 任务状态轮询：排队 5%，运行中 45%，完成/失败 100%
export function useTaskPolling(taskId, interval = 1500) {
  const task = ref(null)
  const timer = ref(null)

  const status = computed(() => task.value?.status || 'queued')
  const progress = computed(() => {
    if (status.value === 'completed' || status.value === 'failed') return 100
    if (status.value === 'running') return 45
    return 5
  })
  const statusLabel = computed(() => {
    const label = STATUS_MAP[status.value]?.label
    return label ? i18n.global.t(label) : status.value
  })

  async function poll() {
    if (!taskId.value) return
    try {
      task.value = await getTask(taskId.value)
      if (task.value.status === 'completed' || task.value.status === 'failed') {
        stop()
      }
    } catch {
      stop()
    }
  }

  function start() {
    stop()
    poll()
    timer.value = window.setInterval(poll, interval)
  }

  function stop() {
    if (timer.value) {
      window.clearInterval(timer.value)
      timer.value = null
    }
  }

  onUnmounted(stop)
  return { task, status, progress, statusLabel, start, stop, poll }
}
