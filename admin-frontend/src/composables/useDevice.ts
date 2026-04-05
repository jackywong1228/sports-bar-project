import { ref, computed, onMounted, onUnmounted } from 'vue'

const TABLET_BREAKPOINT = 1200

export function useDevice() {
  const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1920)

  const isTablet = computed(() => windowWidth.value < TABLET_BREAKPOINT)
  const isTouchDevice = computed(() =>
    typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0)
  )

  let rafId: number | null = null

  function onResize() {
    if (rafId) return
    rafId = requestAnimationFrame(() => {
      windowWidth.value = window.innerWidth
      rafId = null
    })
  }

  onMounted(() => {
    window.addEventListener('resize', onResize, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('resize', onResize)
    if (rafId) cancelAnimationFrame(rafId)
  })

  return { isTablet, isTouchDevice, windowWidth }
}
