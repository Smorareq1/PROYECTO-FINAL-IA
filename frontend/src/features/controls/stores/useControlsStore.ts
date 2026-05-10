import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Command } from '@core/types/commands'
import { sendCommand as sendCmd } from '../services/commandService'

export const useControlsStore = defineStore('controls', () => {
  const lastSent = ref<Command | null>(null)
  const sending = ref(false)
  const error = ref<string | null>(null)

  async function sendCommand(cmd: Command) {
    sending.value = true
    error.value = null
    try {
      await sendCmd(cmd)
      lastSent.value = cmd
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error desconocido'
    } finally {
      sending.value = false
    }
  }

  return { lastSent, sending, error, sendCommand }
})
