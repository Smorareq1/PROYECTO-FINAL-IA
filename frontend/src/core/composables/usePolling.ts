import { onMounted, onUnmounted } from 'vue'

export function usePolling(fn: () => Promise<void>, intervalMs: number) {
  let timer: ReturnType<typeof setInterval> | null = null

  onMounted(() => {
    fn()
    timer = setInterval(fn, intervalMs)
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })
}
