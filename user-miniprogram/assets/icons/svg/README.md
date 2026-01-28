# 首页快捷入口图标 SVG 源文件

> 设计日期：2026-01-28
> 设计规范：高端运动俱乐部/高尔夫会所风格

## 图标列表

| 图标文件 | 功能名称 | 主色 | 设计元素 |
|---------|---------|------|---------|
| venue-entry.svg | 场馆预约 | #1A5D3A | 球场俯视图 |
| coach-entry.svg | 教练预约 | #1A5D3A | 教练+哨子+秒表 |
| food-entry.svg | 在线点餐 | #1A5D3A | 法式餐盖 |
| activity-entry.svg | 活动报名 | #1A5D3A | 日历+举手人物 |
| team-entry.svg | 组队广场 | #1A5D3A | 三人组队 |
| mall-entry.svg | 积分商城 | #1A5D3A | 礼品盒+钻石 |
| member-entry.svg | 会员中心 | #1A5D3A + #C9A962 | 盾牌+金色皇冠 |
| coupon-entry.svg | 我的券包 | #1A5D3A | 票券+折扣符号 |

## 设计规范

- **尺寸**: 48x48 像素 (用于 96rpx 显示)
- **主色**: 墨绿色 `#1A5D3A`
- **金色点缀**: `#C9A962` (仅会员中心使用)
- **线条粗细**: 2px stroke
- **风格**: 圆角线性图标

## 转换为 PNG 方法

### 方法 1: 使用在线工具（推荐）

1. 访问 https://cloudconvert.com/svg-to-png
2. 上传 SVG 文件
3. 设置输出尺寸为 96x96（@2x）或 144x144（@3x）
4. 下载 PNG 文件
5. 重命名为对应的 `-entry.png` 格式

### 方法 2: 使用 Inkscape（免费软件）

```bash
# 安装 Inkscape 后，使用命令行批量转换
inkscape -w 96 -h 96 venue-entry.svg -o ../venue-entry.png
```

### 方法 3: 使用 Node.js + sharp

```bash
npm install sharp
```

```javascript
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const svgFiles = [
  'venue-entry', 'coach-entry', 'food-entry', 'activity-entry',
  'team-entry', 'mall-entry', 'member-entry', 'coupon-entry'
];

svgFiles.forEach(name => {
  sharp(`${name}.svg`)
    .resize(96, 96)
    .png()
    .toFile(`../${name}.png`);
});
```

### 方法 4: 使用 Figma

1. 将 SVG 代码粘贴到 Figma
2. 选中图标，右键 Export
3. 选择 PNG @2x 格式导出

## 颜色变体

如需白色版本（用于深色背景），将 `#1A5D3A` 替换为 `#FFFFFF`。

## 文件结构

```
assets/icons/
├── svg/                 # SVG 源文件（本目录）
│   ├── venue-entry.svg
│   ├── coach-entry.svg
│   ├── food-entry.svg
│   ├── activity-entry.svg
│   ├── team-entry.svg
│   ├── mall-entry.svg
│   ├── member-entry.svg
│   ├── coupon-entry.svg
│   └── README.md
├── venue-entry.png      # PNG 格式（小程序使用）
├── coach-entry.png
├── food-entry.png
├── activity-entry.png
├── team-entry.png
├── mall-entry.png
├── member-entry.png
└── coupon-entry.png
```
