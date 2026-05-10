import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchStatus } from '../services/statusService'

export const useSystemStore = defineStore('system', () => {
  const arduinoConnected = ref(false)
  const modelsLoaded = ref(false)
  const pipelineRunning = ref(false)
  const wsConnected = ref(false)
  const uptimeSeconds = ref(0)
  const cnnModel = ref('')
  const lstmModel = ref('')

  async function refresh() {
    try {
      const data = await fetchStatus()
      arduinoConnected.value = data.arduino_connected
      modelsLoaded.value = data.models_loaded
      pipelineRunning.value = data.pipeline_running
      uptimeSeconds.value = data.uptime_seconds
      cnnModel.value = data.cnn_model
      lstmModel.value = data.lstm_model
    } catch {
      // silently fail — polling will retry
    }
  }

  function setWsConnected(connected: boolean) {
    wsConnected.value = connected
  }

  return {
    arduinoConnected,
    modelsLoaded,
    pipelineRunning,
    wsConnected,
    uptimeSeconds,
    cnnModel,
    lstmModel,
    refresh,
    setWsConnected,
  }
})
