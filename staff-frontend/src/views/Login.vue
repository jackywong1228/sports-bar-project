<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    showToast('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login(username.value, password.value)
    showToast({ message: '登录成功', type: 'success' })
    router.push('/dashboard')
  } catch (_e) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-header">
      <div class="logo-circle">
        <van-icon name="manager" size="48" color="#fff" />
      </div>
      <h1 class="login-title">员工工作台</h1>
      <p class="login-subtitle">场馆体育社交管理系统</p>
    </div>

    <div class="login-form">
      <van-cell-group inset>
        <van-field
          v-model="username"
          label="账号"
          placeholder="请输入用户名"
          left-icon="user-o"
          clearable
        />
        <van-field
          v-model="password"
          type="password"
          label="密码"
          placeholder="请输入密码"
          left-icon="lock"
          @keyup.enter="handleLogin"
        />
      </van-cell-group>

      <div class="login-btn-wrap">
        <van-button
          type="primary"
          block
          round
          size="large"
          :loading="loading"
          loading-text="登录中..."
          @click="handleLogin"
        >
          登 录
        </van-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1A5D3A 0%, #2E7D52 50%, #F5F7F5 50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-header {
  padding-top: 80px;
  text-align: center;
  color: #fff;
}

.logo-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.login-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 4px;
}

.login-subtitle {
  font-size: 14px;
  opacity: 0.8;
  margin: 0;
}

.login-form {
  width: 100%;
  max-width: 400px;
  padding: 0 16px;
  margin-top: 40px;
}

.login-btn-wrap {
  padding: 24px 16px 0;
}
</style>
