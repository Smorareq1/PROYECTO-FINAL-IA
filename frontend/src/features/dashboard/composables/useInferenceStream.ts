import { watch } from 'vue'
import { useInferenceWs } from '@core/composables/useWebSocket'
import { useDashboardStore } from '../stores/useDashboardStore'
import { useSystemStore } from '@features/system/stores/useSystemStore'
import type { IncomingWsMessage, InferenceEvent } from '@core/types/inference'

export function useInferenceStream() {
  const ws = useInferenceWs()
  const dashboardStore = useDashboardStore()
  const systemStore = useSystemStore()

  ws.onMessage((msg: IncomingWsMessage) => {
    if (msg.event) {
      console.log(`[back:${msg.event}] ${msg.message}`, msg.detail ?? {})
      dashboardStore.recordSystem(
        msg.event,
        'back',
        msg.message ?? msg.event,
        msg.detail,
      )
      return
    }

    const inf = msg as unknown as InferenceEvent
    const tag = inf.rejected ? 'REJECTED' : 'OK'
    const conf = ((inf.confidence ?? 0) * 100).toFixed(1)
    const lat = (inf.latency_ms ?? 0).toFixed(1)
    console.log(`[inference] ${tag} · ${inf.command} · conf=${conf}% · lat=${lat}ms`, inf)
    dashboardStore.recordEvent(inf)
  })

  watch(ws.status, (status) => {
    console.log('[inference] WS', status)
    systemStore.setWsConnected(status === 'connected')
  })

  return { wsStatus: ws.status }
}
