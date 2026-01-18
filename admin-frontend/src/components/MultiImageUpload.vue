<template>
  <div class="multi-image-upload">
    <el-upload
      :action="uploadUrl"
      :headers="headers"
      :file-list="fileList"
      list-type="picture-card"
      :before-upload="beforeUpload"
      :on-success="handleSuccess"
      :on-remove="handleRemove"
      :on-preview="handlePreview"
      :on-error="handleError"
      :accept="accept"
      :limit="limit"
      :on-exceed="handleExceed"
      :disabled="disabled"
      multiple
    >
      <el-icon><Plus /></el-icon>
      <template #tip>
        <div class="el-upload__tip">
          支持 {{ acceptText }}，单个文件不超过 {{ maxSize }}MB，最多上传 {{ limit }} 张
        </div>
      </template>
    </el-upload>

    <!-- 图片预览对话框 -->
    <el-dialog v-model="previewVisible" title="图片预览" width="800px">
      <img :src="previewUrl" style="width: 100%" alt="preview" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadProps, UploadUserFile } from 'element-plus'

const props = withDefaults(defineProps<{
  modelValue?: string[]
  accept?: string
  maxSize?: number
  limit?: number
  disabled?: boolean
}>(), {
  modelValue: () => [],
  accept: 'image/*',
  maxSize: 5,
  limit: 9,
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
  (e: 'change', value: string[]): void
}>()

const previewVisible = ref(false)
const previewUrl = ref('')
const fileList = ref<UploadUserFile[]>([])

const acceptText = computed(() => {
  if (props.accept === 'image/*') return 'JPG/PNG/GIF'
  return props.accept
})

const uploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL}/upload/image`
})

const headers = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

// 监听外部值变化，同步到fileList
watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.length > 0) {
    fileList.value = newVal.map((url, index) => ({
      name: `image-${index}`,
      url: url.startsWith('http') ? url : `${import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '')}${url}`,
      response: { data: { url } }
    }))
  } else {
    fileList.value = []
  }
}, { immediate: true })

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }

  const isLtMaxSize = file.size / 1024 / 1024 < props.maxSize
  if (!isLtMaxSize) {
    ElMessage.error(`图片大小不能超过 ${props.maxSize}MB!`)
    return false
  }

  return true
}

const handleSuccess: UploadProps['onSuccess'] = (response: any, uploadFile) => {
  if (response.code === 200 && response.data?.url) {
    uploadFile.response = response
    updateModelValue()
    ElMessage.success('上传成功')
  } else {
    // 移除上传失败的文件
    const index = fileList.value.findIndex(f => f.uid === uploadFile.uid)
    if (index > -1) {
      fileList.value.splice(index, 1)
    }
    ElMessage.error(response.message || '上传失败')
  }
}

const handleRemove: UploadProps['onRemove'] = () => {
  updateModelValue()
}

const handlePreview: UploadProps['onPreview'] = (file) => {
  previewUrl.value = file.url || ''
  previewVisible.value = true
}

const handleError: UploadProps['onError'] = () => {
  ElMessage.error('上传失败，请重试')
}

const handleExceed = () => {
  ElMessage.warning(`最多只能上传 ${props.limit} 张图片`)
}

const updateModelValue = () => {
  const urls = fileList.value
    .filter(f => (f.response as any)?.data?.url)
    .map(f => (f.response as any).data.url)
  emit('update:modelValue', urls)
  emit('change', urls)
}
</script>

<style scoped lang="scss">
.multi-image-upload {
  :deep(.el-upload-list--picture-card) {
    .el-upload-list__item {
      width: 120px;
      height: 120px;
    }
  }

  :deep(.el-upload--picture-card) {
    width: 120px;
    height: 120px;
  }

  .el-upload__tip {
    color: #909399;
    font-size: 12px;
    margin-top: 8px;
  }
}
</style>
