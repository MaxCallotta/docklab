import { defineStore } from 'pinia'
import { environment, getConfig, listEngines, listTemplates } from '../api/system'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    engines: [],
    environment: {},
    config: {},
    templates: []
  }),
  actions: {
    async loadEngines() {
      const data = await listEngines()
      this.engines = data.engines || []
    },
    async loadEnvironment() {
      this.environment = await environment()
    },
    async loadConfig() {
      this.config = await getConfig()
    },
    async loadTemplates() {
      const data = await listTemplates()
      this.templates = data.templates || []
    },
    async loadAll() {
      await Promise.all([this.loadEngines(), this.loadEnvironment(), this.loadConfig(), this.loadTemplates()])
    }
  }
})
