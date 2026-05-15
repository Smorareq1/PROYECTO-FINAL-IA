export function formatConfidence(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function formatLatency(ms: number): string {
  return `${ms.toFixed(1)} ms`
}

export function formatTimestamp(date: Date = new Date()): string {
  return date.toLocaleTimeString('es-GT', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  })
}

export function formatCommandLabel(cmd: string): string {
  return cmd.replace(/_/g, ' ')
}
