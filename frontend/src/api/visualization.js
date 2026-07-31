import http from './http'

export function generatePml(taskId, affinity = null) {
  return http.post('/visualization/pml', { task_id: taskId, affinity })
}

export function openPymol(taskId) {
  return http.post('/visualization/pymol/open', { task_id: taskId })
}
