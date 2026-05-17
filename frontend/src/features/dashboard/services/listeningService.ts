import { httpGet, httpPost } from '@core/api/httpClient'
import type { ListeningStateResponse } from '@core/types/api'

export interface MicDevice {
  index: number
  name: string
  channels: number
  default_sample_rate: number
  is_default: boolean
}

export interface DevicesResponse {
  devices: MicDevice[]
  current: number | null
  current_name: string | null
}

export async function listDevices(): Promise<DevicesResponse> {
  return httpGet<DevicesResponse>('/api/listening/devices')
}

export async function startListening(device?: number | null): Promise<ListeningStateResponse> {
  return httpPost<ListeningStateResponse>('/api/listening/start', {
    device: device ?? null,
  })
}

export async function stopListening(): Promise<ListeningStateResponse> {
  return httpPost<ListeningStateResponse>('/api/listening/stop')
}
