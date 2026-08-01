import axios from 'axios'
import { ElMessage } from 'element-plus'
import i18n from '../i18n'

function localize(message) {
  if (message && i18n.global.te(message)) {
    return i18n.global.t(message)
  }
  return message
}

// 统一 axios 实例：后端返回 {code,message,data} 时自动解包 data
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 600000
})

http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code !== 200) {
        const message = localize(body.msg || '请求失败')
        ElMessage.error(message)
        return Promise.reject(new Error(message))
      }
      return body.data
    }
    return body
  },
  (error) => {
    const message =
      localize(error.response?.data?.msg || error.message) || i18n.global.t('网络请求失败，请检查后端服务')
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default http
