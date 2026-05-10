import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { InferenceEvent } from '@core/types/inference'
import { ALL_COMMANDS } from '@core/types/commands'
import { MAX_LOG_ENTRIES, MAX_LATENCY_POINTS } from '@core/utils/constants'

export interface LogEntry extends InferenceEvent {
  timestamp: string
}

export const useDashboardStore = defineStore('dashboard', () => {
  const lastEvent = ref<InferenceEvent | null>(null)
  const log = ref<LogEntry[]>([])
  const latencies = ref<number[]>([])
  const latencyLabels = ref<string[]>([])
  const countByClass = ref<Record<string, number>>({})

  const totalPredictions = ref(0)
  const acceptedPredictions = ref(0)

  const avgLatency = computed(() => {
    if (latencies.value.length === 0) return 0
    return latencies.value.reduce((a, b) => a + b, 0) / latencies.value.length
  })

  function recordEvent(event: InferenceEvent) {
    lastEvent.value = event
    totalPredictions.value++

    if (!event.rejected) {
      acceptedPredictions.value++
      countByClass.value[event.command] = (countByClass.value[event.command] ?? 0) + 1
    }

    latencies.value.push(event.latency_ms)
    if (latencies.value.length > MAX_LATENCY_POINTS) latencies.value.shift()

    const now = new Date()
    const timeLabel = now.toLocaleTimeString('es-GT', { hour12: false })
    latencyLabels.value.push(timeLabel)
    if (latencyLabels.value.length > MAX_LATENCY_POINTS) latencyLabels.value.shift()

    const entry: LogEntry = {
      ...event,
      timestamp: now.toLocaleTimeString('es-GT', { hour12: false, fractionalSecondDigits: 3 }),
    }
    log.value.unshift(entry)
    if (log.value.length > MAX_LOG_ENTRIES) log.value.pop()
  }

  function getCountForCommands(): number[] {
    return ALL_COMMANDS.map(cmd => countByClass.value[cmd] ?? 0)
  }

  return {
    lastEvent,
    log,
    latencies,
    latencyLabels,
    countByClass,
    totalPredictions,
    acceptedPredictions,
    avgLatency,
    recordEvent,
    getCountForCommands,
  }
})
