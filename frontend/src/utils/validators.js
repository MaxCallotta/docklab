import { ElMessage } from 'element-plus'
import { MAX_UPLOAD_MB } from './constants'
import i18n from '../i18n'

function t(key, params) {
  return i18n.global.t(key, params)
}

export function validateUploadFile(file, allowedExtensions, maxSizeMB = MAX_UPLOAD_MB) {
  const dot = file.name.lastIndexOf('.')
  const ext = dot > 0 ? file.name.slice(dot).toLowerCase() : ''
  if (!allowedExtensions.includes(ext)) {
    ElMessage.error(t('仅支持 {extensions} 文件', { extensions: allowedExtensions.join(' / ') }))
    return false
  }
  if (file.size > maxSizeMB * 1024 * 1024) {
    ElMessage.error(t('文件超过 {max} MB 限制', { max: maxSizeMB }))
    return false
  }
  return true
}

export function validatePdbId(value) {
  if (!/^[0-9][A-Za-z0-9]{3}$/.test(value.trim())) {
    ElMessage.error(t('PDB ID 应为 4 位字符，首位为数字'))
    return false
  }
  return true
}

export function validateSmiles(value) {
  if (!value || !value.trim()) {
    ElMessage.error(t('请输入 SMILES 字符串'))
    return false
  }
  if (!/^[A-Za-z0-9@+\-\\[\]()#.%*:=\/]+$/.test(value.trim())) {
    ElMessage.error(t('SMILES 包含非法字符'))
    return false
  }
  return true
}

export function validateNumber(value, min, max, name) {
  const num = Number(value)
  if (!Number.isFinite(num) || num < min || num > max) {
    ElMessage.error(t('{name} 需在 {min} ~ {max} 之间', { name, min, max }))
    return false
  }
  return true
}

export function validateBox(box) {
  const sizeOk =
    validateNumber(box.size_x, 1, 200, '盒子尺寸 X') &&
    validateNumber(box.size_y, 1, 200, '盒子尺寸 Y') &&
    validateNumber(box.size_z, 1, 200, '盒子尺寸 Z')
  const centerOk =
    validateNumber(box.center_x, -2000, 2000, '盒子中心 X') &&
    validateNumber(box.center_y, -2000, 2000, '盒子中心 Y') &&
    validateNumber(box.center_z, -2000, 2000, '盒子中心 Z')
  return sizeOk && centerOk
}
