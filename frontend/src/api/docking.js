import http from './http'

export function runDocking(payload) {
  return http.post('/docking/run', payload)
}

export function autoPocket(payload) {
  return http.post('/docking/auto-pocket', payload)
}
