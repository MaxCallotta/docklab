import http from './http'

export function health() {
  return http.get('/system/health')
}

export function listEngines() {
  return http.get('/system/engines')
}

export function environment() {
  return http.get('/system/environment')
}

export function getConfig() {
  return http.get('/system/config')
}

export function saveConfig(payload) {
  return http.post('/system/config', payload)
}

export function listTemplates() {
  return http.get('/system/templates')
}

export function saveTemplate(payload) {
  return http.post('/system/templates', payload)
}

export function deleteTemplate(name) {
  return http.delete(`/system/templates/${encodeURIComponent(name)}`)
}

export function getLogs(params) {
  return http.get('/system/logs', { params })
}
