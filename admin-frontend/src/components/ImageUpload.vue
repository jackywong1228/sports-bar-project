<template>
  <div class="image-upload">
    <el-upload
      :action="uploadUrl"
      :headers="headers"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :on-success="handleSuccess"
      :on-error="handleError"
      :accept="accept"
      :disabled="disabled"
      class="uploader"
    >
      <div v-if="imageUrl" class="image-preview">
        <img :src="fullImageUrl" alt="preview" />
        <div class="image-actions">
          <el-icon class="action-icon" @click.stop="handlePreview"><ZoomIn /></el-icon>
          <el-icon class="action-icon" @click.stop="handleRemove"><Delete /></el-icon>
        </div>
      </div>
      <div v-else class="upload-placeholder">
        <el-icon class="upload-icon"><Plus /></el-icon>
        <div class="upload-text">{{ placeholder }}</div>
      </div>
    </el-upload>

    <!-- 图片预览对话框 -->
    <el-dialog v-model="previewVisible" title="图片预览" width="800px">
      <img :src="fullImageUrl" style="width: 100%" alt="preview" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Plus, ZoomIn, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadProps } from 'element-plus'

const props = withDefaults(defineProps<{
  modelValue?: string
  placeholder?: string
  accept?: string
  maxSize?: number // MB
  disabled?: boolean
  folder?: string
}>(), {
  modelValue: '',
  placeholder: '点击上传图片',
  accept: 'image/*',
  maxSize: 5,
  disabled: false,
  folder: 'images'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}>()

const previewVisible = ref(false)
const uploading = ref(false)

const imageUrl = computed(() => props.modelValue)

const fullImageUrl = computed(() => {
  if (!imageUrl.value) return ''
  if (imageUrl.value.startsWith('http')) return imageUrl.value
  return `${import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '')}${imageUrl.value}`
})

const uploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL}/upload/image`
})

const headers = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

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

  uploading.value = true
  return true
}

const handleSuccess: UploadProps['onSuccess'] = (response: any) => {
  uploading.value = false
  if (response.code === 200 && response.data?.url) {
    emit('update:modelValue', response.data.url)
    emit('change', response.data.url)
    ElMessage.success('上传成功')
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleError: UploadProps['onError'] = () => {
  uploading.value = false
  ElMessage.error('上传失败，请重试')
}

const handlePreview = () => {
  previewVisible.value = true
}

const handleRemove = () => {
  emit('update:modelValue', '')
  emit('change', '')
}
</script>

<style scoped lang="scss">
.image-upload {
  .uploader {
    :deep(.el-upload) {
      border: 1px dashed #d9d9d9;
      border-radius: 8px;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      transition: all 0.3s;

      &:hover {
        border-color: #409eff;
      }
    }
  }

  .upload-placeholder {
    width: 148px;
    height: 148px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #fafafa;

    .upload-icon {
      font-size: 28px;
      color: #8c939d;
    }

    .upload-text {
      margin-top: 8px;
      font-size: 12px;
      color: #8c939d;
    }
  }

  .image-preview {
    width: 148px;
    height: 148px;
    position: relative;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .image-actions {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      opacity: 0;
      transition: opacity 0.3s;

      .action-icon {
        font-size: 20px;
        color: #fff;
        cursor: pointer;
        transition: transform 0.2s;

        &:hover {
          transform: scale(1.2);
        }
      }
    }

    &:hover .image-actions {
      opacity: 1;
    }
  }
}
</style>
