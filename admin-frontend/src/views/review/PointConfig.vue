<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>评论积分配置</span>
        </div>
      </template>

      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="140px" style="max-width: 500px;">
        <el-form-item label="基础积分" prop="base_points">
          <el-input-number v-model="formData.base_points" :min="0" style="width: 100%;" />
          <div class="form-tip">每条评论获得的基础积分</div>
        </el-form-item>
        <el-form-item label="文字奖励积分" prop="text_bonus">
          <el-input-number v-model="formData.text_bonus" :min="0" style="width: 100%;" />
          <div class="form-tip">包含文字评价时额外获得的积分</div>
        </el-form-item>
        <el-form-item label="图片奖励积分" prop="image_bonus">
          <el-input-number v-model="formData.image_bonus" :min="0" style="width: 100%;" />
          <div class="form-tip">包含图片时额外获得的积分</div>
        </el-form-item>
        <el-form-item label="每日上限" prop="daily_limit">
          <el-input-number v-model="formData.daily_limit" :min="0" style="width: 100%;" />
          <div class="form-tip">每人每日通过评论获得的积分上限（0表示不限）</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { getReviewPointConfig, updateReviewPointConfig } from '@/api/review'

const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  base_points: 5,
  text_bonus: 3,
  image_bonus: 5,
  daily_limit: 50
})

const formRules = {
  base_points: [{ required: true, message: '请输入基础积分', trigger: 'blur' }],
  text_bonus: [{ required: true, message: '请输入文字奖励积分', trigger: 'blur' }],
  image_bonus: [{ required: true, message: '请输入图片奖励积分', trigger: 'blur' }],
  daily_limit: [{ required: true, message: '请输入每日上限', trigger: 'blur' }]
}

const fetchConfig = async () => {
  loading.value = true
  try {
    const res = await getReviewPointConfig()
    if (res.data) {
      Object.assign(formData, res.data)
    }
  } catch (e) {
    console.error('获取评论积分配置失败:', e)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    await updateReviewPointConfig({ ...formData })
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.form-tip { font-size: 12px; color: #999; }
</style>
