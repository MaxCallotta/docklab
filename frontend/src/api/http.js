import axios from 'axios'
import { ElMessage } from 'element-plus'

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
        ElMessage.error(body.msg || '请求失败')
        return Promise.reject(new Error(body.msg || '请求失败'))
      }
      return body.data
    }
    return body
  },
  (error) => {
    const message =
      error.response?.data?.msg || error.message || '网络请求失败，请检查后端服务'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default http
