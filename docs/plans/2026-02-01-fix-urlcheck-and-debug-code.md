# 修复 Code Review HIGH 级别问题实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 code review 发现的 HIGH 级别安全配置问题，清理调试代码

**Architecture:** 恢复微信小程序的 urlCheck 安全配置，移除临时网络调试代码

**Tech Stack:** 微信小程序

---

## 问题分析

| 严重程度 | 文件 | 问题 |
|---------|------|------|
| HIGH | `project.private.config.json` | `urlCheck: false` 关闭了域名校验 |
| MEDIUM | `app.js` | 调试用网络测试代码（console.log 等） |

---

## Task 1: 恢复 urlCheck 安全配置

**Files:**
- Modify: `user-miniprogram/project.private.config.json:5`

**Step 1: 修改配置文件**

将 `urlCheck` 从 `false` 改回 `true`：

```json
{
  "libVersion": "3.13.2",
  "projectname": "user-miniprogram",
  "setting": {
    "urlCheck": true,
    ...
  }
}
```

**Step 2: 验证修改**

Run: `git diff user-miniprogram/project.private.config.json`

Expected: 看到 `urlCheck` 从 `false` 变为 `true`

**Step 3: 提交**

```bash
git add user-miniprogram/project.private.config.json
git commit -m "fix: 恢复 urlCheck 安全配置"
```

---

## Task 2: 清理调试网络测试代码

**Files:**
- Modify: `user-miniprogram/app.js:71-118`

**Step 1: 移除多余的网络测试**

当前代码包含 4 个测试请求（百度、httpbin、静态端点等），这些是调试用代码。

选项 A（推荐）- 简化为单一测试：
```javascript
testNetwork() {
  const testUrl = `${this.globalData.baseUrl}/member/venue-types`
  console.log('[NETWORK TEST] 测试:', testUrl)

  wx.request({
    url: testUrl,
    method: 'GET',
    timeout: 10000,
    success: (res) => {
      console.log('[NETWORK TEST] 成功, statusCode:', res.statusCode)
    },
    fail: (err) => {
      console.error('[NETWORK TEST] 失败:', err.errMsg)
    }
  })
}
```

选项 B - 完全移除 testNetwork 函数（如果不再需要调试）

**Step 2: 验证修改**

Run: `git diff user-miniprogram/app.js`

Expected: 看到调试代码被简化或移除

**Step 3: 提交**

```bash
git add user-miniprogram/app.js
git commit -m "chore: 清理网络调试代码"
```

---

## Task 3: 最终验证

**Step 1: 检查 git status**

Run: `git status`

Expected: 工作区干净，所有更改已提交

**Step 2: 在微信开发者工具中测试**

- 打开小程序项目
- 确认 urlCheck 生效（开发者工具应显示域名校验警告如有非白名单域名）
- 确认基本功能正常

---

## 决策点

在执行 Task 2 之前需要确认：

1. **网络问题是否已解决？** 如果仍在调试 SSL/网络问题，可暂时保留调试代码
2. **选择哪个方案？**
   - 选项 A: 简化调试代码（保留基本测试能力）
   - 选项 B: 完全移除（网络问题已解决）

---

**计划完成，已保存到 `docs/plans/2026-02-01-fix-urlcheck-and-debug-code.md`**