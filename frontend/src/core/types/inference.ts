import type { Command } from './commands'

export interface InferenceEvent {
  command: Command
  confidence: number
  latency_ms: number
  rejected: boolean
  manual?: boolean
  timestamp?: string
}

export type SystemEventKind =
  | 'mic_start'
  | 'mic_stop'
  | 'mic_chunks'
  | 'audio_ws_open'
  | 'audio_ws_close'
  | 'audio_recv'
  | 'vad_trigger'
  | 'error'

export interface SystemEvent {
  kind: SystemEventKind
  origin: 'front' | 'back'
  message: string
  detail?: Record<string, unknown>
}

export interface IncomingWsMessage {
  // Mismo canal /ws/inference para predicciones y eventos del sistema
  event?: SystemEventKind   // si está presente, es evento de sistema (back)
  origin?: 'back'
  message?: string
  detail?: Record<string, unknown>
  // si no, son predicciones (campos de InferenceEvent)
  command?: string
  confidence?: number
  latency_ms?: number
  rejected?: boolean
  manual?: boolean
  reason?: string
}
