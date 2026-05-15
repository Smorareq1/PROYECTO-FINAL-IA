import type { Command } from './commands'

export interface InferenceEvent {
  command: Command
  confidence: number
  latency_ms: number
  rejected: boolean
  manual?: boolean
  timestamp?: string
}
