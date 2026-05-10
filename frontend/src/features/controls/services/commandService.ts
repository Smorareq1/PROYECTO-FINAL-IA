import { httpPost } from '@core/api/httpClient'
import type { Command } from '@core/types/commands'

export async function sendCommand(cmd: Command): Promise<void> {
  await httpPost(`/api/command/${cmd}`)
}
