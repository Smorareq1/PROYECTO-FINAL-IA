import { ref, type Ref } from 'vue'
import { WS_RECONNECT_DELAY_MS } from '@core/utils/constants'

export type WsStatus = 'connecting' | 'connected' | 'disconnected'

export interface WsClient<T> {
  status: Ref<WsStatus>
  connect: () => void
  disconnect: () => void
  onMessage: (handler: (data: T) => void) => void
}

export function createWsClient<T>(path: string): WsClient<T> {
  const status = ref<WsStatus>('disconnected')
  let ws: WebSocket | null = null
  let handler: ((data: T) => void) | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let intentionalClose = false

  function getWsUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}${path}`
  }

  function connect() {
    intentionalClose = false
    status.value = 'connecting'
    ws = new WebSocket(getWsUrl())

    ws.onopen = () => {
      status.value = 'connected'
    }

    ws.onmessage = (event: MessageEvent) => {
      if (handler) {
        const data = JSON.parse(event.data as string) as T
        handler(data)
      }
    }

    ws.onclose = () => {
      status.value = 'disconnected'
      ws = null
      if (!intentionalClose) {
        reconnectTimer = setTimeout(connect, WS_RECONNECT_DELAY_MS)
      }
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function disconnect() {
    intentionalClose = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
    ws = null
    status.value = 'disconnected'
  }

  function onMessage(h: (data: T) => void) {
    handler = h
  }

  return { status, connect, disconnect, onMessage }
}
