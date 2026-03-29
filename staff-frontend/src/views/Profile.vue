<script setup lang="ts">
import { showDialog } from 'vant'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const handleLogout = async () => {
  try {
    await showDialog({
      title: '确认退出',
      message: '确定要退出登录吗？'
    })
    userStore.logout()
  } catch (_e) {
    // 取消
  }
}
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="个人中心" :border="false" class="top-bar" />

    <!-- 用户信息 -->
    <div class="user-section">
      <van-image
        :src="userStore.userInfo?.avatar || ''"
        width="64"
        height="64"
        round
        fit="cover"
      >
        <template #error>
          <van-icon name="user-o" size="36" color="#ddd" />
        </template>
      </van-image>
      <div class="user-info">
        <div class="user-name">{{ userStore.userInfo?.name || userStore.userInfo?.username || '-' }}</div>
        <div class="user-role">{{ (userStore.userInfo?.roles || []).join(', ') || '员工' }}</div>
      </div>
    </div>

    <!-- 功能列表 -->
    <van-cell-group inset class="menu-group">
      <van-cell title="账号" :value="userStore.userInfo?.username || '-'" icon="user-o" />
      <van-cell title="手机号" :value="userStore.userInfo?.phone || '-'" icon="phone-o" />
    </van-cell-group>

    <!-- 退出登录 -->
    <div class="logout-section">
      <van-button type="danger" plain block round size="large" @click="handleLogout">
        退出登录
      </van-button>
    </div>
  </div>
</template>

<style scoped>
.top-bar {
  background: var(--staff-primary);
}

.top-bar :deep(.van-nav-bar__title) {
  color: #fff;
  font-weight: 600;
}

.user-section {
  background: linear-gradient(135deg, var(--staff-primary), var(--staff-primary-light));
  padding: 24px 16px 32px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: #fff;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
}

.user-role {
  font-size: 13px;
  opacity: 0.8;
  margin-top: 4px;
}

.menu-group {
  margin-top: -12px;
}

.logout-section {
  padding: 32px 16px;
}
</style>
