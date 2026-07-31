import { defineStore } from 'pinia'
import { listTasks } from '../api/task'

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [],
    loading: false,
    pollingTimer: null
  }),
  getters: {
    runningCount: (state) => state.tasks.filter((t) => t.status === 'running').length
  },
  actions: {
    async loadTasks(status) {
      this.loading = true
      try {
        const data = await listTasks(status)
        this.tasks = data.tasks || []
      } finally {
        this.loading = false
      }
    },
    startPolling(interval = 3000) {
      this.stopPolling()
      this.pollingTimer = window.setInterval(() => this.loadTasks(), interval)
    },
    stopPolling() {
      if (this.pollingTimer) {
        window.clearInterval(this.pollingTimer)
        this.pollingTimer = null
      }
    }
  }
})
