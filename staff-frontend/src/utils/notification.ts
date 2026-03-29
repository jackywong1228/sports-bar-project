// 用 Web Audio API 生成提示音
export function playNotificationSound() {
  try {
    const ctx = new AudioContext()
    const playTone = (freq: number, startTime: number, duration: number) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = freq
      osc.type = 'sine'
      gain.gain.setValueAtTime(0.5, startTime)
      gain.gain.exponentialRampToValueAtTime(0.01, startTime + duration)
      osc.start(startTime)
      osc.stop(startTime + duration)
    }
    const now = ctx.currentTime
    for (let round = 0; round < 2; round++) {
      const offset = round * 0.6
      playTone(880, now + offset, 0.15)
      playTone(1100, now + offset + 0.18, 0.15)
      playTone(1320, now + offset + 0.36, 0.2)
    }
  } catch (e) {
    console.warn('无法播放提示音:', e)
  }
}

// 手机振动
export function vibrate(duration: number = 200) {
  try {
    if (navigator.vibrate) {
      navigator.vibrate(duration)
    }
  } catch (e) {
    console.warn('振动不可用:', e)
  }
}
