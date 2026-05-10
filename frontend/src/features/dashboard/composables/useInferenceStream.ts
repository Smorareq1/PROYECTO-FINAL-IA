import { watch } from 'vue'
import { useInferenceWs } from '@core/composables/useWebSocket'
import { useDashboardStore } from '../stores/useDashboardStore'
import { useSystemStore } from '@features/system/stores/useSystemStore'

export function useInferenceStream() {
  const ws = useInferenceWs()
  const dashboardStore = useDashboardStore()
  const systemStore = useSystemStore()

  ws.onMessage((event) => {
    dashboardStore.recordEvent(event)
  })

  watch(ws.status, (status) => {
    systemStore.setWsConnected(status === 'connected')
  })

  return { wsStatus: ws.status }
}
