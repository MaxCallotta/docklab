import http from './http'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export function prepareLigand(file) {
  const form = new FormData()
  form.append('file', file)
  return http.post('/molecules/prepare-ligand', form)
}

export function prepareReceptorFile(file) {
  const form = new FormData()
  form.append('file', file)
  return http.post('/molecules/prepare-receptor', form)
}

export function prepareReceptorPdbId(pdbId) {
  const form = new FormData()
  form.append('pdb_id', pdbId)
  return http.post('/molecules/prepare-receptor', form)
}

export function prepareSmiles(smiles) {
  return http.post('/molecules/prepare-smiles', { smiles })
}

// 生成可被 3Dmol 直接 fetch 的本地文件访问 URL
export function previewUrl(localPath) {
  return `${API_BASE}/molecules/preview?path=${encodeURIComponent(localPath)}`
}
