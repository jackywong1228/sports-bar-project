import request from '@/utils/request'

// 上传图片
export function uploadImage(file: File, folder?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (folder) {
    formData.append('folder', folder)
  }
  return request.post('/upload/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 批量上传图片
export function uploadImages(files: File[], folder?: string) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  if (folder) {
    formData.append('folder', folder)
  }
  return request.post('/upload/images', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 上传文件
export function uploadFile(file: File, folder?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (folder) {
    formData.append('folder', folder)
  }
  return request.post('/upload/file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 删除文件
export function deleteFile(path: string) {
  return request.delete('/upload/file', { data: { path } })
}

// 获取上传配置
export function getUploadConfig() {
  return request.get('/upload/config')
}
