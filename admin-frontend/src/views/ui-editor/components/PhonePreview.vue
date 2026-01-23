<script setup lang="ts">
import { computed } from 'vue'
import type { UIBlockConfig, UIMenuItem } from '../types'

const props = defineProps<{
  blocks: UIBlockConfig[]
  quickEntries: UIMenuItem[]
  tabBarItems: UIMenuItem[]
}>()

// 过滤出可见的区块
const visibleBlocks = computed(() => {
  return props.blocks.filter(b => b.is_active)
})

// 可见的快捷入口
const visibleQuickEntries = computed(() => {
  return props.quickEntries.filter(m => m.is_visible)
})

// 可见的TabBar
const visibleTabBarItems = computed(() => {
  return props.tabBarItems.filter(m => m.is_visible)
})

// 检查区块是否可见
const isBlockVisible = (blockType: string) => {
  return visibleBlocks.value.some(b => b.block_type === blockType)
}

// 生成 SVG 占位图的辅助函数
const createPlaceholder = (width: number, height: number, bgColor: string, textColor: string, text: string) => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
    <rect fill="${bgColor}" width="${width}" height="${height}"/>
    <text fill="${textColor}" font-family="Arial,sans-serif" font-size="14" x="50%" y="50%" text-anchor="middle" dominant-baseline="middle">${text}</text>
  </svg>`
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

// 模拟数据
const mockBanners = [
  { image: createPlaceholder(375, 180, '#1a5d3a', '#ffffff', 'Banner 1'), title: '轮播图1' },
  { image: createPlaceholder(375, 180, '#2d7a4e', '#ffffff', 'Banner 2'), title: '轮播图2' }
]

const mockVenues = [
  { id: 1, name: '羽毛球场', image: createPlaceholder(120, 80, '#f0f0f0', '#333333', '场地1'), price: 50 },
  { id: 2, name: '篮球场', image: createPlaceholder(120, 80, '#f0f0f0', '#333333', '场地2'), price: 80 },
  { id: 3, name: '网球场', image: createPlaceholder(120, 80, '#f0f0f0', '#333333', '场地3'), price: 100 }
]

const mockActivities = [
  { id: 1, title: '周末羽毛球友谊赛', image: createPlaceholder(120, 80, '#f0f0f0', '#333333', '活动1') },
  { id: 2, title: '篮球3v3比赛', image: createPlaceholder(120, 80, '#f0f0f0', '#333333', '活动2') }
]
</script>

<template>
  <div class="phone-preview">
    <div class="phone-frame">
      <!-- 状态栏 -->
      <div class="status-bar">
        <span class="time">9:41</span>
        <div class="status-icons">
          <span class="signal"></span>
          <span class="wifi"></span>
          <span class="battery"></span>
        </div>
      </div>

      <!-- 导航栏 -->
      <div class="nav-bar">
        <span class="nav-title">运动社交</span>
      </div>

      <!-- 页面内容 -->
      <div class="page-content">
        <!-- 轮播图 -->
        <div class="block banner-block" v-if="isBlockVisible('banner')">
          <div class="banner-item">
            <img :src="mockBanners[0]?.image" alt="banner" />
          </div>
          <div class="banner-dots">
            <span class="dot active"></span>
            <span class="dot"></span>
          </div>
        </div>

        <!-- 快捷入口 -->
        <div class="block quick-entry-block" v-if="isBlockVisible('quick_entry')">
          <div class="quick-entry-grid">
            <div
              class="quick-entry-item"
              v-for="item in visibleQuickEntries.slice(0, 8)"
              :key="item.id"
            >
              <div class="entry-icon">
                <img v-if="item.icon" :src="item.icon" alt="" />
                <div v-else class="icon-placeholder"></div>
              </div>
              <span class="entry-title">{{ item.title }}</span>
            </div>
          </div>
        </div>

        <!-- 热门场馆 -->
        <div class="block list-block" v-if="isBlockVisible('list')">
          <div class="block-header">
            <span class="block-title">热门场馆</span>
            <span class="block-more">更多 ></span>
          </div>
          <div class="venue-list">
            <div class="venue-card" v-for="venue in mockVenues" :key="venue.id">
              <img :src="venue.image" alt="" class="venue-image" />
              <div class="venue-info">
                <span class="venue-name">{{ venue.name }}</span>
                <span class="venue-price">¥{{ venue.price }}/小时</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 热门活动 -->
        <div class="block scroll-block" v-if="isBlockVisible('scroll')">
          <div class="block-header">
            <span class="block-title">热门活动</span>
            <span class="block-more">更多 ></span>
          </div>
          <div class="activity-scroll">
            <div class="activity-card" v-for="activity in mockActivities" :key="activity.id">
              <img :src="activity.image" alt="" class="activity-image" />
              <span class="activity-title">{{ activity.title }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- TabBar -->
      <div class="tab-bar" v-if="visibleTabBarItems.length > 0">
        <div
          class="tab-item"
          v-for="(item, index) in visibleTabBarItems"
          :key="item.id"
          :class="{ active: index === 0 }"
        >
          <div class="tab-icon">
            <img v-if="item.icon" :src="index === 0 && item.icon_active ? item.icon_active : item.icon" alt="" />
            <div v-else class="icon-placeholder"></div>
          </div>
          <span class="tab-title">{{ item.title }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.phone-preview {
  display: flex;
  justify-content: center;
}

.phone-frame {
  width: 375px;
  height: 812px;
  background: #fff;
  border-radius: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}

.phone-frame::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 150px;
  height: 30px;
  background: #1a1a1a;
  border-radius: 0 0 20px 20px;
  z-index: 10;
}

.status-bar {
  height: 44px;
  padding: 12px 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #1a5d3a;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.status-icons {
  display: flex;
  gap: 4px;
}

.signal,
.wifi,
.battery {
  width: 18px;
  height: 12px;
  background: #fff;
  border-radius: 2px;
}

.nav-bar {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a5d3a;
  color: #fff;
}

.nav-title {
  font-size: 17px;
  font-weight: 600;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  background: #f5f7f5;
}

.block {
  background: #fff;
  margin-bottom: 10px;
}

.banner-block {
  position: relative;
}

.banner-item img {
  width: 100%;
  height: 180px;
  object-fit: cover;
}

.banner-dots {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.5);
}

.dot.active {
  width: 18px;
  background: #fff;
}

.quick-entry-block {
  padding: 16px;
}

.quick-entry-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.quick-entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.entry-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #f0f5f0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.entry-icon img {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.icon-placeholder {
  width: 24px;
  height: 24px;
  background: #ddd;
  border-radius: 4px;
}

.entry-title {
  font-size: 12px;
  color: #333;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60px;
}

.list-block,
.scroll-block {
  padding: 16px;
}

.block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.block-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.block-more {
  font-size: 12px;
  color: #999;
}

.venue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.venue-card {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: #f8f9f8;
  border-radius: 8px;
}

.venue-image {
  width: 80px;
  height: 60px;
  border-radius: 6px;
  object-fit: cover;
}

.venue-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.venue-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.venue-price {
  font-size: 13px;
  color: #1a5d3a;
  font-weight: 600;
}

.activity-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.activity-card {
  flex-shrink: 0;
  width: 140px;
}

.activity-image {
  width: 140px;
  height: 90px;
  border-radius: 8px;
  object-fit: cover;
}

.activity-title {
  display: block;
  font-size: 13px;
  color: #333;
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tab-bar {
  height: 60px;
  display: flex;
  background: #fff;
  border-top: 1px solid #eee;
  padding-bottom: 10px;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.tab-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-icon img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.tab-title {
  font-size: 10px;
  color: #999;
}

.tab-item.active .tab-title {
  color: #1a5d3a;
}
</style>
