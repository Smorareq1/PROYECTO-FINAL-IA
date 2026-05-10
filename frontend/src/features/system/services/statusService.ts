import { httpGet } from '@core/api/httpClient'
import type { StatusResponse, HealthResponse, MetricsResponse } from '@core/types/api'

export async function fetchStatus(): Promise<StatusResponse> {
  return httpGet<StatusResponse>('/api/status')
}

export async function fetchHealth(): Promise<HealthResponse> {
  return httpGet<HealthResponse>('/api/health')
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  return httpGet<MetricsResponse>('/api/metrics')
}
