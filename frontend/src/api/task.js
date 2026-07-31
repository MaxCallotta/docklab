import http from './http'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export function createTask(payload) {
  return http.post('/tasks', payload)
}

export function listTasks(status) {
  return http.get('/tasks', { params: status ? { status } : {} })
}

export function getTask(taskId) {
  return http.get(`/tasks/${taskId}`)
}

export function restartTask(taskId) {
  return http.post(`/tasks/${taskId}/restart`)
}

export function deleteTask(taskId) {
  return http.delete(`/tasks/${taskId}`)
}

export function batchDelete(taskIds) {
  return http.post('/tasks/batch-delete', { task_ids: taskIds })
}

export function downloadTaskUrl(taskId) {
  return `${API_BASE}/tasks/${taskId}/download`
}

export function taskFileUrl(taskId, kind, filename) {
  return `${API_BASE}/tasks/${taskId}/files/${kind}/${encodeURIComponent(filename)}`
}

export function poseUrl(taskId, poseIndex) {
  return `${API_BASE}/tasks/${taskId}/pose/${poseIndex}`
}

export function exportPose(taskId, poseIndex, format = 'pdbqt') {
  return http.post(`/tasks/${taskId}/export-pose`, { pose_index: poseIndex, format })
}
