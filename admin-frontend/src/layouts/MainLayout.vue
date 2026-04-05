<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useDevice } from '@/composables/useDevice'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { isTablet } = useDevice()

const isCollapse = ref(false)
const drawerVisible = ref(false)

// iPad 抽屉菜单：展开的子菜单索引
const expandedMenu = ref<string | null>(null)

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

// 面包屑
const breadcrumbs = computed(() => {
  const crumbs: { title: string; path?: string }[] = []
  for (const item of menuList) {
    if (item.children) {
      const child = item.children.find(c => route.path.startsWith(c.path))
      if (child) {
        crumbs.push({ title: item.title })
        crumbs.push({ title: child.title })
        return crumbs
      }
    } else if (route.path === item.path) {
      crumbs.push({ title: item.title })
      return crumbs
    }
  }
  return crumbs
})

// 抽屉菜单方法
function toggleSubmenu(path: string) {
  expandedMenu.value = expandedMenu.value === path ? null : path
}

function navigateTo(path: string) {
  router.push(path)
  drawerVisible.value = false
}

function isChildActive(item: { path: string; children?: { path: string }[] }): boolean {
  if (!item.children) return route.path === item.path
  return item.children.some(c => route.path.startsWith(c.path))
}

// 切换到 PC 模式时关闭抽屉
watch(isTablet, (val) => {
  if (!val) drawerVisible.value = false
})

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
  <div class="layout" :class="{ 'is-tablet': isTablet }">
    <!-- ====== PC: 固定侧边栏（原有代码完全保留） ====== -->
    <el-aside v-if="!isTablet" :width="isCollapse ? '64px' : '220px'" class="layout-aside">
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
          <el-menu-item v-else :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <!-- ====== iPad: 抽屉导航 ====== -->
    <el-drawer
      v-if="isTablet"
      v-model="drawerVisible"
      direction="ltr"
      :size="280"
      :show-close="false"
      :with-header="false"
      class="drawer-nav"
    >
      <div class="drawer-logo">
        <span>场馆管理系统</span>
      </div>
      <nav class="drawer-menu">
        <template v-for="item in menuList" :key="item.path">
          <!-- 有子菜单 -->
          <template v-if="item.children">
            <div
              class="drawer-menu-item drawer-menu-parent"
              :class="{ active: isChildActive(item) }"
              @click="toggleSubmenu(item.path)"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
              <el-icon class="arrow" :class="{ expanded: expandedMenu === item.path }">
                <ArrowDown />
              </el-icon>
            </div>
            <div class="drawer-submenu" :class="{ open: expandedMenu === item.path }">
              <div
                v-for="child in item.children"
                :key="child.path"
                class="drawer-menu-item drawer-menu-child"
                :class="{ active: route.path.startsWith(child.path) }"
                @click="navigateTo(child.path)"
              >
                <span>{{ child.title }}</span>
              </div>
            </div>
          </template>
          <!-- 无子菜单 -->
          <div
            v-else
            class="drawer-menu-item"
            :class="{ active: route.path === item.path }"
            @click="navigateTo(item.path)"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </div>
        </template>
      </nav>
    </el-drawer>

    <!-- ====== 主区域 ====== -->
    <div class="layout-main-wrapper">
      <!-- 头部 -->
      <header class="layout-header">
        <div class="header-left">
          <!-- iPad: 汉堡按钮 -->
          <el-icon
            v-if="isTablet"
            class="hamburger-btn"
            @click="drawerVisible = true"
          >
            <Operation />
          </el-icon>
          <!-- PC: 折叠按钮 -->
          <el-icon
            v-else
            class="collapse-btn"
            @click="isCollapse = !isCollapse"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <!-- iPad: 面包屑 -->
          <el-breadcrumb v-if="isTablet && breadcrumbs.length" separator="/" class="header-breadcrumb">
            <el-breadcrumb-item v-for="(crumb, i) in breadcrumbs" :key="i">
              {{ crumb.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
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
      </header>

      <!-- 主内容区 -->
      <main class="layout-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ====== 通用布局 ====== */
.layout {
  display: flex;
  height: 100vh;
  height: 100dvh;
}

.layout-main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* ====== PC 侧边栏（保持原有样式） ====== */
.layout-aside {
  background-color: #304156;
  transition: width 0.3s;
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
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

/* ====== 头部 ====== */
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 0 20px;
  height: 60px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
}

.hamburger-btn {
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.hamburger-btn:active {
  background-color: #f0f2f5;
}

.header-breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
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

/* ====== 主内容区 ====== */
.layout-content {
  flex: 1;
  background-color: #f0f2f5;
  padding: var(--content-padding, 20px);
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* ====== iPad 抽屉导航 ====== */
.drawer-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background-color: #263445;
}

.drawer-menu {
  padding: 8px 0;
}

.drawer-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 48px;
  padding: 0 20px;
  color: #bfcbd9;
  font-size: 15px;
  cursor: pointer;
  transition: background-color 0.2s;
  -webkit-user-select: none;
  user-select: none;
}

.drawer-menu-item:active {
  background-color: #263445;
}

.drawer-menu-item.active {
  color: #409eff;
  background-color: #263445;
}

.drawer-menu-parent {
  justify-content: flex-start;
}

.drawer-menu-parent .arrow {
  margin-left: auto;
  font-size: 12px;
  transition: transform 0.3s;
}

.drawer-menu-parent .arrow.expanded {
  transform: rotate(180deg);
}

.drawer-submenu {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
  background-color: #263445;
}

.drawer-submenu.open {
  max-height: 300px;
}

.drawer-menu-child {
  padding-left: 52px;
  height: 44px;
  font-size: 14px;
}

/* ====== iPad 头部调整 ====== */
.is-tablet .layout-header {
  height: 50px;
  padding: 0 12px;
}

.is-tablet .user-name {
  display: none;
}
</style>

<!-- 抽屉全局样式（必须 unscoped） -->
<style>
.drawer-nav .el-drawer__body {
  padding: 0;
  background-color: #304156;
}
</style>
