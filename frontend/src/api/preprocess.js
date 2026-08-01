import axios from 'axios'

const preprocessHttp = axios.create({
  baseURL: '/api',
  timeout: 600000
})

function unwrap(response) {
  const body = response.data
  if (body && typeof body === 'object' && 'code' in body) {
    if (body.code !== 200) {
      throw new Error(body.msg || '预处理请求失败')
    }
    return body.data
  }
  return body
}

export async function uploadPreprocessFiles(files, sessionId) {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  if (sessionId) {
    form.append('session_id', sessionId)
  }
  const response = await preprocessHttp.post('/preprocess/upload', form)
  return unwrap(response)
}

export async function runPreprocess(payload) {
  const response = await preprocessHttp.post('/preprocess/run', payload)
  return unwrap(response)
}

export async function getPreprocessStatus(batchId) {
  const response = await preprocessHttp.get(`/preprocess/status/${batchId}`)
  return unwrap(response)
}

export function preprocessDownloadUrl(fileId, filename = 'result.sdf') {
  return `/api/preprocess/download/${fileId}/${encodeURIComponent(filename)}`
}

export function preprocessBatchDownloadUrl(batchId) {
  return `/api/preprocess/download/batch/${batchId}`
}
