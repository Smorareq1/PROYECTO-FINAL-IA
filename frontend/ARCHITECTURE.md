# Arquitectura Frontend — Panel Domotico (Dashboard)

## Stack Tecnologico

| Tecnologia | Version | Proposito |
|---|---|---|
| Vue | 3.x | Framework principal (Composition API) |
| Vite | 5.x | Build tool y dev server |
| TypeScript | 5.x | Tipado estatico |
| Pinia | 2.x | State management |
| Vue Router | 4.x | Enrutamiento SPA |
| Chart.js | 4.x | Graficas de confianza y latencia |
| vue-chartjs | 5.x | Wrapper de Chart.js para Vue |
| TailwindCSS | 3.x | Utilidades CSS |
| Axios | 1.x | Cliente HTTP para la API REST |
| Docker + nginx | alpine | Servir build de produccion |

## Estructura de Carpetas

```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── .env                                # VITE_API_URL=http://localhost:8000
├── .env.production                     # VITE_API_URL=/api (reverse proxy)
│
├── public/
│   └── favicon.ico
│
├── src/
│   ├── main.ts                         # Entry point
│   ├── App.vue                         # Root component
│   │
│   ├── router/
│   │   └── index.ts                    # Rutas de la SPA
│   │
│   ├── stores/                         # Pinia stores
│   │   ├── inference.ts                # Estado de inferencias en vivo (WebSocket)
│   │   ├── system.ts                   # Estado del sistema (Arduino, modelos)
│   │   └── metrics.ts                  # Metricas agregadas
│   │
│   ├── composables/                    # Logica reutilizable (Composition API)
│   │   ├── useWebSocket.ts             # Conexion WebSocket al backend
│   │   ├── useAudioLevel.ts            # Nivel de audio en tiempo real
│   │   └── useLatency.ts               # Calculo de latencias
│   │
│   ├── services/                       # Comunicacion con el backend
│   │   ├── api.ts                      # Instancia Axios configurada
│   │   ├── statusService.ts            # GET /api/status, /api/health
│   │   ├── commandService.ts           # POST /api/command/{cmd}
│   │   └── metricsService.ts           # GET /api/metrics
│   │
│   ├── components/                     # Componentes Vue
│   │   ├── layout/
│   │   │   ├── AppHeader.vue           # Header con titulo y status
│   │   │   ├── AppSidebar.vue          # Sidebar con controles manuales
│   │   │   └── AppFooter.vue           # Footer con info del sistema
│   │   │
│   │   ├── dashboard/
│   │   │   ├── ListeningIndicator.vue  # LED virtual verde/amarillo/rojo
│   │   │   ├── LastCommand.vue         # Ultimo comando reconocido (texto grande)
│   │   │   ├── ConfidenceChart.vue     # Grafica de barras por clase
│   │   │   ├── LatencyChart.vue        # Grafica de latencias (ultimas 30)
│   │   │   ├── CommandLog.vue          # Log scrolleable con timestamps
│   │   │   └── SystemStatus.vue        # Estado Arduino + modelos
│   │   │
│   │   ├── controls/
│   │   │   ├── ManualCommandPanel.vue  # Botones para enviar comandos manualmente
│   │   │   ├── CommandButton.vue       # Boton individual de comando
│   │   │   └── ThresholdSlider.vue     # Ajuste de umbral de confianza
│   │   │
│   │   └── common/
│   │       ├── StatusBadge.vue         # Badge de estado (conectado/desconectado)
│   │       ├── MetricCard.vue          # Tarjeta con metrica individual
│   │       └── LoadingSpinner.vue      # Indicador de carga
│   │
│   ├── views/
│   │   ├── DashboardView.vue           # Vista principal del panel domotico
│   │   └── MetricsView.vue             # Vista de metricas detalladas
│   │
│   ├── types/
│   │   ├── inference.ts                # Tipos de prediccion, comando, etc.
│   │   ├── system.ts                   # Tipos de estado del sistema
│   │   └── api.ts                      # Tipos de respuestas de la API
│   │
│   └── assets/
│       └── styles/
│           └── main.css                # Estilos globales + Tailwind imports
│
├── Dockerfile
├── nginx.conf                          # Config nginx para produccion
└── .dockerignore
```

## Reglas de Arquitectura

### 1. Composition API exclusivamente

- Todos los componentes usan `<script setup lang="ts">`.
- No se usa Options API.
- Logica reutilizable se extrae a `composables/`.

### 2. Tipado estricto con TypeScript

- Todos los archivos `.ts` y `.vue` tienen tipado completo.
- Los tipos de la API se definen en `types/` y se comparten entre stores y services.
- `tsconfig.json` con `strict: true`.

### 3. Estado centralizado en Pinia

- El estado de inferencias en vivo (`inference store`) se alimenta via WebSocket.
- El estado del sistema (`system store`) se obtiene por polling cada 5 segundos via REST.
- Las metricas agregadas (`metrics store`) se obtienen bajo demanda.

### 4. Comunicacion con el Backend

- **WebSocket** (`ws://localhost:8000/ws/inference`): stream en vivo de predicciones. Cada mensaje contiene:
  ```json
  {
    "command": "ENCIENDE",
    "confidence": 0.94,
    "latency_ms": 85,
    "rejected": false
  }
  ```
- **REST API**: para estado del sistema, comandos manuales y metricas.
- En produccion, nginx hace reverse proxy de `/api` y `/ws` al backend.

### 5. Separacion de responsabilidades

- **`services/`**: comunicacion HTTP pura con el backend. No contienen estado.
- **`stores/`**: estado reactivo de la aplicacion. Consumen los services.
- **`composables/`**: logica reutilizable (WebSocket, calculos). No dependen de componentes.
- **`components/`**: solo presentacion y binding a stores. No hacen llamadas HTTP directas.
- **`views/`**: composicion de componentes por ruta. No contienen logica de negocio.

### 6. Dashboard en tiempo real

El dashboard debe mostrar:
- Indicador de escucha (LED virtual verde/amarillo/rojo)
- Ultimo comando reconocido (texto grande, animado al cambiar)
- Grafica de barras con confianza por clase (Chart.js)
- Grafica de latencia (ultimas 30 inferencias)
- Botones manuales para cada comando (5 simples + 4 compuestos)
- Log scrolleable con timestamps
- Estado de conexion con Arduino

### 7. Responsividad

- El dashboard debe funcionar en pantalla completa en un proyector durante la defensa.
- Disenar primero para pantallas grandes (1920x1080 minimo).
- Usar Tailwind para breakpoints si se necesita soporte mobile.

### 8. Sin dependencias externas en runtime

- No se hacen llamadas a CDNs externos. Todo se bundlea con Vite.
- Compatible con modo avion (una vez cargado el frontend en el navegador).

## Comandos del Panel

Los 9 botones manuales del panel domotico:

| Comando | Tipo | Descripcion |
|---|---|---|
| ENCIENDE | Simple | Cierra rele |
| APAGA | Simple | Abre rele |
| IZQUIERDA | Simple | Motor pasos antihorario |
| DERECHA | Simple | Motor pasos horario |
| DETENTE | Simple | Beep + todo apagado |
| ENCIENDE_RAPIDO | Compuesto | Rele + LED RGB blanco |
| ENCIENDE_LENTO | Compuesto | Rele + LED RGB azul tenue |
| GIRA_IZQUIERDA | Compuesto | Motor 1024 antihorario |
| GIRA_DERECHA | Compuesto | Motor 1024 horario |
