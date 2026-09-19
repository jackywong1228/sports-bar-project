// 自毁 Service Worker：用于清除旧版 admin PWA 在客户端残留的缓存与注册。
// 旧 sw.js（workbox 生成）曾注册在根作用域，会劫持 /staff/、/coach/ 等路径。
// 本文件部署后，浏览器发现 sw.js 内容变化 → 安装本 SW → 清空所有缓存 → 注销自身 → 重载页面。
self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys()
      await Promise.all(keys.map((k) => caches.delete(k)))
    } catch (e) { /* ignore */ }
    try {
      await self.registration.unregister()
    } catch (e) { /* ignore */ }
    try {
      const clients = await self.clients.matchAll({ type: 'window' })
      clients.forEach((c) => c.navigate(c.url))
    } catch (e) { /* ignore */ }
  })())
})

// 不拦截任何请求：全部直走网络
self.addEventListener('fetch', () => {})
