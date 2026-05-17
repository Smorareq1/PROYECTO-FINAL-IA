import { onMounted, onUnmounted } from 'vue'
import { createWsClient, type WsClient } from '@core/api/wsClient'
import type { IncomingWsMessage } from '@core/types/inference'

let sharedClient: WsClient<IncomingWsMessage> | null = null

export function useInferenceWs() {
  if (!sharedClient) {
    sharedClient = createWsClient<IncomingWsMessage>('/ws/inference')
  }

  onMounted(() => {
    sharedClient!.connect()
  })

  onUnmounted(() => {
    // don't disconnect — other components may be using it
  })

  return sharedClient
}
