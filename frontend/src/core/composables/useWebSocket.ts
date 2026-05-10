import { onMounted, onUnmounted } from 'vue'
import { createWsClient, type WsClient } from '@core/api/wsClient'
import type { InferenceEvent } from '@core/types/inference'

let sharedClient: WsClient<InferenceEvent> | null = null

export function useInferenceWs() {
  if (!sharedClient) {
    sharedClient = createWsClient<InferenceEvent>('/ws/inference')
  }

  onMounted(() => {
    sharedClient!.connect()
  })

  onUnmounted(() => {
    // don't disconnect — other components may be using it
  })

  return sharedClient
}
