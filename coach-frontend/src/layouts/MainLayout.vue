<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const active = ref('schedule')

watch(
  () => route.path,
  (path) => {
    if (path.startsWith('/courses')) active.value = 'courses'
    else if (path.startsWith('/profile')) active.value = 'profile'
    else active.value = 'schedule'
  },
  { immediate: true }
)

const onChange = (name: string) => {
  router.push(`/${name}`)
}
</script>

<template>
  <div class="main-layout">
    <div class="layout-content">
      <router-view />
    </div>
    <van-tabbar :model-value="active" @change="onChange" fixed placeholder>
      <van-tabbar-item name="schedule" icon="calendar-o">排课</van-tabbar-item>
      <van-tabbar-item name="courses" icon="orders-o">课程</van-tabbar-item>
      <van-tabbar-item name="profile" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<style scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-content {
  flex: 1;
}
</style>
