export interface StatusResponse {
  arduino_connected: boolean
  models_loaded: boolean
  pipeline_running: boolean
  cnn_model: string
  lstm_model: string
  uptime_seconds: number
}

export interface HealthResponse {
  status: string
  models_loaded: boolean
  arduino_connected: boolean
}

export interface MetricsResponse {
  total_predictions: number
  accepted_predictions: number
  rejected_predictions: number
  predictions_by_class: Record<string, number>
  avg_latency_ms: number
  avg_confidence: number
}
