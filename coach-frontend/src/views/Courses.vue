<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMyCourses, type CoachCourse } from '@/api/course'

const CATEGORY_COLORS: Record<string, string> = {
  group: '#07c160',
  golf: '#1989fa',
  squash: '#ff976a',
  pickleball: '#ee0a24'
}

const courses = ref<CoachCourse[]>([])
const loading = ref(false)

const fetchCourses = async () => {
  loading.value = true
  try {
    const res = await getMyCourses()
    courses.value = res.data as unknown as CoachCourse[]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCourses()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">我的课程</div>
      <div class="page-subtitle">共 {{ courses.length }} 门在售课程</div>
    </div>

    <van-loading v-if="loading" class="loading-wrap" size="32" color="#1A5D3A" />

    <template v-else>
      <van-empty v-if="courses.length === 0" description="暂无课程" />

      <div v-for="c in courses" :key="c.id" class="course-card">
        <img v-if="c.cover_image" :src="c.cover_image" class="course-cover" alt="" />
        <div v-else class="course-cover course-cover-placeholder">
          {{ c.category_text }}
        </div>
        <div class="course-body">
          <div class="course-title-row">
            <span class="course-title">{{ c.title }}</span>
            <van-tag
              v-if="c.category"
              :color="CATEGORY_COLORS[c.category] || '#999'"
              class="category-tag"
            >
              {{ c.category_text }}
            </van-tag>
          </div>
          <div v-if="c.subtitle" class="course-subtitle">{{ c.subtitle }}</div>
          <div class="course-meta">
            <span class="course-price">{{ c.price }} 金币</span>
            <span class="course-meta-item">{{ c.duration_minutes }} 分钟</span>
            <span class="course-meta-item">未来课次 {{ c.upcoming_session_count }}</span>
          </div>
          <div class="course-status">{{ c.status_text }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-header {
  padding: 20px 16px 12px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #1A1A1A;
}

.page-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #999;
}

.loading-wrap {
  display: block;
  margin: 60px auto;
}

.course-card {
  display: flex;
  background: #fff;
  margin: 0 16px 12px;
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.course-cover {
  width: 88px;
  height: 88px;
  flex-shrink: 0;
  border-radius: 8px;
  object-fit: cover;
}

.course-cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--coach-primary) 0%, var(--coach-primary-light) 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.course-body {
  flex: 1;
  min-width: 0;
  margin-left: 12px;
  display: flex;
  flex-direction: column;
}

.course-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.course-title {
  font-size: 15px;
  font-weight: 600;
  color: #1A1A1A;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-tag {
  flex-shrink: 0;
  border-radius: 4px;
}

.course-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.course-price {
  color: #FF6034;
  font-weight: 600;
}

.course-meta-item {
  color: #666;
  font-size: 12px;
}

.course-status {
  margin-top: auto;
  padding-top: 6px;
  font-size: 12px;
  color: var(--coach-primary);
}
</style>
