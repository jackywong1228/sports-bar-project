<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const userStore = useUserStore()

const isCollapse = ref(false)

const menuList = [
  {
    path: '/dashboard',
    title: '首页',
    icon: 'HomeFilled'
  },
  {
    path: '/member',
    title: '会员管理',
    icon: 'User',
    children: [
      { path: '/member/list', title: '会员列表' },
      { path: '/member/level', title: '会员等级' },
      { path: '/member/card', title: '会员卡套餐' },
      { path: '/member/card-order', title: '会员卡订单' }
    ]
  },
  {
    path: '/venue',
    title: '场地管理',
    icon: 'Location',
    children: [
      { path: '/venue/list', title: '场地列表' },
      { path: '/venue/type', title: '场地类型' },
      { path: '/venue/price', title: '价格管理' }
    ]
  },
  {
    path: '/reservation',
    title: '预约管理',
    icon: 'Calendar',
    children: [
      { path: '/reservation/list', title: '预约记录' }
    ]
  },
  {
    path: '/coach',
    title: '教练管理',
    icon: 'Avatar',
    children: [
      { path: '/coach/list', title: '教练列表' },
      { path: '/coach/application', title: '教练申请' }
    ]
  },
  {
    path: '/activity',
    title: '活动管理',
    icon: 'Flag',
    children: [
      { path: '/activity/list', title: '活动列表' }
    ]
  },
  {
    path: '/food',
    title: '点餐管理',
    icon: 'Food',
    children: [
      { path: '/food/category', title: '餐饮分类' },
      { path: '/food/list', title: '餐饮商品' },
      { path: '/food/order', title: '餐饮订单' }
    ]
  },
  {
    path: '/coupon',
    title: '票券管理',
    icon: 'Ticket',
    children: [
      { path: '/coupon/template', title: '优惠券模板' },
      { path: '/coupon/record', title: '发放记录' }
    ]
  },
  {
    path: '/mall',
    title: '积分商城',
    icon: 'ShoppingCart',
    children: [
      { path: '/mall/category', title: '商品分类' },
      { path: '/mall/product', title: '积分商品' },
      { path: '/mall/order', title: '兑换订单' }
    ]
  },
  {
    path: '/finance',
    title: '财务管理',
    icon: 'Wallet',
    children: [
      { path: '/finance/overview', title: '财务概览' },
      { path: '/finance/recharge', title: '充值记录' },
      { path: '/finance/consume', title: '消费记录' },
      { path: '/finance/settlement', title: '教练结算' }
    ]
  },
  {
    path: '/message',
    title: '消息通知',
    icon: 'Bell',
    children: [
      { path: '/message/send', title: '消息管理' },
      { path: '/message/template', title: '消息模板' },
      { path: '/message/announcement', title: '公告管理' },
      { path: '/message/banner', title: '轮播图管理' }
    ]
  },
  {
    path: '/ui-assets',
    title: '小程序管理',
    icon: 'Cellphone',
    children: [
      { path: '/ui-editor', title: '布局编辑器' },
      { path: '/ui-assets/icon', title: '图标管理' },
      { path: '/ui-assets/theme', title: '主题配色' },
      { path: '/ui-assets/image', title: '图片素材' }
    ]
  },
  {
    path: '/system',
    title: '系统管理',
    icon: 'Setting',
    children: [
      { path: '/system/user', title: '用户管理' },
      { path: '/system/role', title: '角色管理' },
      { path: '/system/department', title: '部门管理' }
    ]
  }
]

const activeMenu = computed(() => route.path)

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
  } catch {
    // 取消
  }
}
</script>

<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo">
        <span v-if="!isCollapse">场馆管理系统</span>
        <span v-else>场</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="layout-menu"
      >
        <template v-for="item in menuList" :key="item.path">
          <!-- 有子菜单 -->
          <el-sub-menu v-if="item.children" :index="item.path">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.path"
              :index="child.path"
            >
              {{ child.title }}
            </el-menu-item>
          </el-sub-menu>
          <!-- 无子菜单 -->
          <el-menu-item v-else :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 头部 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            @click="isCollapse = !isCollapse"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="user-name">{{ userStore.userInfo?.name }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-aside {
  background-color: #304156;
  transition: width 0.3s;
  overflow-y: auto;
  overflow-x: hidden;
}

.layout-aside::-webkit-scrollbar {
  width: 6px;
}

.layout-aside::-webkit-scrollbar-thumb {
  background: #4a5568;
  border-radius: 3px;
}

.layout-aside::-webkit-scrollbar-track {
  background: transparent;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background-color: #263445;
}

.layout-menu {
  border-right: none;
  background-color: #304156;
}

.layout-menu:not(.el-menu--collapse) {
  width: 220px;
}

:deep(.el-menu) {
  background-color: #304156;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: #bfcbd9;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: #263445;
}

:deep(.el-menu-item.is-active) {
  color: #409eff;
  background-color: #263445;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 0 20px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.user-name {
  margin-left: 8px;
  font-size: 14px;
}

.layout-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
