<script setup lang="ts">
import { computed } from 'vue'
import { showConfirmDialog } from 'vant'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const userInfo = computed(() => userStore.userInfo)
const initial = computed(() => (userStore.userInfo?.name || '').charAt(0))

const onLogout = async () => {
  try {
    await showConfirmDialog({
      title: '提示',
      message: '确定要退出登录吗？'
    })
    userStore.logout()
  } catch {
    // 用户取消
  }
}
</script>

<template>
  <div class="page-container">
    <!-- 用户信息卡 -->
    <div class="user-card">
      <img v-if="userInfo?.avatar" :src="userInfo.avatar" class="avatar" alt="" />
      <div v-else class="avatar avatar-placeholder">{{ initial }}</div>
      <div class="user-info">
        <div class="user-name">{{ userInfo?.name || '教练' }}</div>
        <div class="user-no">工号：{{ userInfo?.coach_no || '-' }}</div>
      </div>
      <div v-if="userInfo?.rating" class="rating">评分 {{ userInfo.rating }}</div>
    </div>

    <!-- 信息列表 -->
    <van-cell-group class="info-group">
      <van-cell title="姓名" :value="userInfo?.name || '-'" />
      <van-cell title="教练类型" :value="userInfo?.type_name || userInfo?.type || '-'" />
      <van-cell title="手机号" :value="userInfo?.phone || '-'" />
      <van-cell title="工号" :value="userInfo?.coach_no || '-'" />
    </van-cell-group>

    <!-- 退出登录 -->
    <div class="logout-wrap">
      <van-button type="danger" block round @click="onLogout">退出登录</van-button>
    </div>
  </div>
</template>

<style scoped>
.user-card {
  display: flex;
  align-items: center;
  margin: 20px 16px 16px;
  padding: 24px 20px;
  background: linear-gradient(135deg, var(--coach-primary) 0%, var(--coach-primary-light) 100%);
  border-radius: 16px;
  color: #fff;
}

.avatar {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.25);
  font-size: 26px;
  font-weight: 600;
}

.user-info {
  flex: 1;
  min-width: 0;
  margin-left: 16px;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
}

.user-no {
  margin-top: 6px;
  font-size: 13px;
  opacity: 0.85;
}

.rating {
  flex-shrink: 0;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 4px 10px;
}

.info-group {
  margin: 0 16px;
  border-radius: 12px;
  overflow: hidden;
}

.logout-wrap {
  margin: 32px 16px;
}
</style>
