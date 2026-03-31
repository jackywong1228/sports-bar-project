<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { getActivityDetail, createActivity, updateActivity, deleteActivity } from '@/api/activity'

const router = useRouter()
const route = useRoute()

const activityId = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})
const isEdit = computed(() => !!activityId.value)
const pageTitle = computed(() => isEdit.value ? '编辑活动' : '新建活动')

const submitting = ref(false)
const form = ref({
  title: '',
  cover_image: '',
  description: '',
  content: '',
  start_time: '',
  end_time: '',
  registration_deadline: '',
  location: '',
  max_participants: 0,
  price: 0,
  status: 'draft',
  tags: ''
})

// 将后端时间格式 "YYYY-MM-DD HH:MM" 转为 input datetime-local 格式 "YYYY-MM-DDTHH:MM"
const toLocalInput = (val: string) => {
  if (!val) return ''
  return val.replace(' ', 'T').slice(0, 16)
}

// 将 input datetime-local 格式转为后端时间格式
const fromLocalInput = (val: string) => {
  if (!val) return ''
  return val.replace('T', ' ').slice(0, 16)
}

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('staff_token')
  return { Authorization: `Bearer ${token}` }
})

const uploadUrl = computed(() => {
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  return `${base}/upload/image?folder=activities`
})

const onUploadSuccess = (response: any) => {
  if (response?.data?.url) {
    form.value.cover_image = response.data.url
  }
}

const coverFileList = computed(() => {
  if (form.value.cover_image) {
    return [{ url: form.value.cover_image }]
  }
  return []
})

const onDeleteCover = () => {
  form.value.cover_image = ''
  return true
}

const validate = (): boolean => {
  if (!form.value.title.trim()) {
    showToast('请输入活动标题')
    return false
  }
  if (!form.value.start_time) {
    showToast('请选择开始时间')
    return false
  }
  if (!form.value.end_time) {
    showToast('请选择结束时间')
    return false
  }
  if (form.value.end_time <= form.value.start_time) {
    showToast('结束时间必须晚于开始时间')
    return false
  }
  return true
}

const onSubmit = async (asDraft = true) => {
  if (!validate()) return
  submitting.value = true
  try {
    const data: Record<string, unknown> = { ...form.value }
    data.status = asDraft ? 'draft' : 'published'
    data.max_participants = Number(data.max_participants) || 0
    data.price = Number(data.price) || 0

    if (isEdit.value) {
      await updateActivity(activityId.value!, data)
      showToast({ message: '更新成功', type: 'success' })
    } else {
      await createActivity(data)
      showToast({ message: asDraft ? '已保存草稿' : '发布成功', type: 'success' })
    }
    router.back()
  } catch (_e) {
    // request.ts already handles errors
  } finally {
    submitting.value = false
  }
}

const onDelete = async () => {
  if (!activityId.value) return
  try {
    await showDialog({
      title: '确认删除',
      message: '删除后不可恢复，确定删除此活动吗？'
    })
    await deleteActivity(activityId.value)
    showToast({ message: '已删除', type: 'success' })
    router.back()
  } catch (_e) {
    // 取消
  }
}

const loadDetail = async () => {
  if (!activityId.value) return
  try {
    const res = await getActivityDetail(activityId.value)
    const d = res.data
    form.value = {
      title: d.title || '',
      cover_image: d.cover_image || '',
      description: d.description || '',
      content: d.content || '',
      start_time: fromLocalInput(d.start_time || ''),
      end_time: fromLocalInput(d.end_time || ''),
      registration_deadline: fromLocalInput(d.registration_deadline || ''),
      location: d.location || '',
      max_participants: d.max_participants || 0,
      price: d.price || 0,
      status: d.status || 'draft',
      tags: d.tags || ''
    }
  } catch (_e) {
    showToast('加载活动详情失败')
    router.back()
  }
}

onMounted(() => {
  if (isEdit.value) loadDetail()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar :title="pageTitle" left-arrow @click-left="router.back()">
      <template #right>
        <span v-if="isEdit" class="delete-btn" @click="onDelete">删除</span>
      </template>
    </van-nav-bar>

    <van-form class="form-content">
      <!-- 基础信息 -->
      <van-cell-group inset title="基础信息">
        <van-field v-model="form.title" label="活动标题" placeholder="请输入活动标题" required />
        <van-field v-model="form.description" label="活动简介" type="textarea" rows="2" placeholder="一句话描述活动" />
        <van-field v-model="form.content" label="活动详情" type="textarea" rows="4" placeholder="详细内容、注意事项等" />
        <van-field label="封面图片">
          <template #input>
            <van-uploader
              :file-list="coverFileList"
              :max-count="1"
              :headers="uploadHeaders"
              :action="uploadUrl"
              @success="onUploadSuccess"
              @delete="onDeleteCover"
            />
          </template>
        </van-field>
      </van-cell-group>

      <!-- 时间地点 -->
      <van-cell-group inset title="时间与地点">
        <van-field label="开始时间" required>
          <template #input>
            <input
              type="datetime-local"
              class="native-datetime"
              :value="toLocalInput(form.start_time)"
              @input="form.start_time = fromLocalInput(($event.target as HTMLInputElement).value)"
            />
          </template>
        </van-field>
        <van-field label="结束时间" required>
          <template #input>
            <input
              type="datetime-local"
              class="native-datetime"
              :value="toLocalInput(form.end_time)"
              @input="form.end_time = fromLocalInput(($event.target as HTMLInputElement).value)"
            />
          </template>
        </van-field>
        <van-field label="报名截止">
          <template #input>
            <input
              type="datetime-local"
              class="native-datetime"
              :value="toLocalInput(form.registration_deadline)"
              @input="form.registration_deadline = fromLocalInput(($event.target as HTMLInputElement).value)"
              placeholder="可选"
            />
          </template>
        </van-field>
        <van-field v-model="form.location" label="活动地点" placeholder="例如：一号场馆" />
      </van-cell-group>

      <!-- 报名设置 -->
      <van-cell-group inset title="报名设置">
        <van-field v-model="form.max_participants" label="人数上限" type="digit" placeholder="0 表示不限制" />
        <van-field v-model="form.price" label="报名费用" type="number" placeholder="0 表示免费">
          <template #button>
            <span class="unit-text">金币</span>
          </template>
        </van-field>
        <van-field v-model="form.tags" label="标签" placeholder="逗号分隔，如：瑜伽,初级" />
      </van-cell-group>

      <!-- 提交按钮 -->
      <div class="submit-area">
        <van-button round block plain type="primary" :loading="submitting" @click="onSubmit(true)">
          {{ isEdit ? '保存' : '保存草稿' }}
        </van-button>
        <van-button round block type="primary" :loading="submitting" @click="onSubmit(false)" style="margin-top: 12px">
          {{ isEdit ? '保存并发布' : '立即发布' }}
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<style scoped>
.form-content {
  padding-bottom: 120px;
}

.delete-btn {
  color: #ee0a24;
  font-size: 14px;
}

.unit-text {
  color: #999;
  font-size: 14px;
}

.submit-area {
  padding: 24px 16px;
}

.native-datetime {
  border: none;
  background: transparent;
  font-size: 14px;
  color: #323233;
  width: 100%;
  padding: 0;
  outline: none;
}
</style>
