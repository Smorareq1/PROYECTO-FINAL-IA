# Arquitectura Frontend — Panel Domotico (Dashboard)

> Clean Architecture: `core/` para infraestructura compartida, `features/` para modulos de negocio autocontenidos.

## Stack Tecnologico

| Tecnologia | Version | Proposito |
|---|---|---|
| Vue | 3.x | Framework principal (Composition API + `<script setup>`) |
| Vite | 5.x | Build tool y dev server |
| TypeScript | 5.x | Tipado estatico (`strict: true`) |
| Pinia | 2.x | State management reactivo |
| Vue Router | 4.x | Enrutamiento SPA |
| Chart.js | 4.x | Graficas de confianza y latencia |
| vue-chartjs | 5.x | Wrapper de Chart.js para Vue |
| TailwindCSS | 3.x | Utilidades CSS sobre los design tokens |
| Docker + nginx | alpine | Servir build de produccion |

## Estructura de Carpetas

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── .env                                    # VITE_API_BASE_URL=http://localhost:8000
├── .env.production                         # VITE_API_BASE_URL=  (reverse proxy)
│
├── public/
│   └── favicon.ico
│
├── src/
│   ├── main.ts                             # Bootstrap: createApp, plugins, router, pinia
│   ├── App.vue                             # Root: <RouterView /> + layout shell
│   │
│   ├── core/                               # ── INFRAESTRUCTURA COMPARTIDA ──
│   │   │                                   #    No conoce features. Features importan de core.
│   │   │
│   │   ├── api/                            # Clientes HTTP y WebSocket
│   │   │   ├── httpClient.ts               # fetch wrapper con base URL, error handling, tipos
│   │   │   └── wsClient.ts                 # WebSocket con reconexion automatica y tipado
│   │   │
│   │   ├── design-system/                  # ── DESIGN SYSTEM ──
│   │   │   ├── tokens/                     # Valores primitivos (fuente unica de verdad visual)
│   │   │   │   ├── colors.ts               # Paleta: bg, surface, text, accent, semantic (success/danger/warning)
│   │   │   │   ├── spacing.ts              # Escala: 4px base (xs=4, sm=8, md=16, lg=24, xl=32, 2xl=48)
│   │   │   │   ├── typography.ts           # Font families, sizes, weights, line-heights
│   │   │   │   ├── radii.ts               # Border radii (sm=6, md=8, lg=12, xl=16, full=9999)
│   │   │   │   ├── shadows.ts             # Box shadows (sm, md, lg, glow)
│   │   │   │   ├── transitions.ts         # Duraciones y easings
│   │   │   │   └── index.ts               # Re-export de todos los tokens
│   │   │   │
│   │   │   └── components/                 # Componentes base (atomicos, sin logica de negocio)
│   │   │       ├── BaseButton.vue          # Variantes: primary, ghost, danger; sizes: sm, md, lg
│   │   │       ├── BaseCard.vue            # Contenedor con borde, padding, titulo opcional
│   │   │       ├── BaseBadge.vue           # Indicador de estado (dot + label)
│   │   │       ├── BaseIcon.vue            # Wrapper de iconos SVG inline
│   │   │       ├── BaseInput.vue           # Input con label y error state
│   │   │       ├── BaseSlider.vue          # Range input estilizado
│   │   │       ├── BaseSpinner.vue         # Indicador de carga animado
│   │   │       └── BaseTooltip.vue         # Tooltip posicional
│   │   │
│   │   ├── layout/                         # Shell de la aplicacion
│   │   │   ├── AppShell.vue                # Grid principal (header + sidebar + main + footer)
│   │   │   ├── AppHeader.vue               # Titulo + indicadores de estado
│   │   │   ├── AppSidebar.vue              # Panel lateral colapsable
│   │   │   └── AppFooter.vue               # Info del sistema, version
│   │   │
│   │   ├── composables/                    # Logica reutilizable (no atada a features)
│   │   │   ├── useWebSocket.ts             # Conexion WS tipada con reconexion y estado reactivo
│   │   │   └── usePolling.ts               # Polling generico con intervalo configurable
│   │   │
│   │   ├── types/                          # Tipos compartidos
│   │   │   ├── api.ts                      # Tipos de respuestas del backend (StatusResponse, etc.)
│   │   │   ├── commands.ts                 # Enum Command, CommandType, CommandMeta
│   │   │   └── inference.ts                # InferenceEvent, ModelOutput, Prediction
│   │   │
│   │   └── utils/                          # Helpers puros (sin estado, sin side effects)
│   │       ├── formatters.ts               # formatConfidence, formatLatency, formatTimestamp
│   │       └── constants.ts                # MAX_LOG_ENTRIES, POLL_INTERVAL_MS, etc.
│   │
│   └── features/                           # ── MODULOS DE NEGOCIO ──
│       │                                   #    Cada feature es autocontenida.
│       │                                   #    Puede importar de core/ pero NUNCA de otra feature.
│       │
│       ├── dashboard/                      # Feature: vista principal del panel domotico
│       │   ├── DashboardView.vue           # Vista raiz (compone los componentes)
│       │   ├── stores/
│       │   │   └── useDashboardStore.ts    # Estado local: ultimo comando, historial, latencias
│       │   ├── composables/
│       │   │   └── useInferenceStream.ts   # Conecta WS y alimenta el store
│       │   └── components/
│       │       ├── CommandDisplay.vue       # Comando reconocido (texto grande + animacion)
│       │       ├── ListeningIndicator.vue   # LED virtual (verde/amarillo/rojo)
│       │       ├── ConfidenceChart.vue      # Barras de predicciones por clase
│       │       ├── LatencyChart.vue         # Linea de latencia en tiempo real
│       │       ├── PredictionLog.vue        # Log scrolleable con timestamps
│       │       └── StatsBar.vue             # Total, aceptados, latencia promedio
│       │
│       ├── controls/                       # Feature: controles manuales del Arduino
│       │   ├── ControlsPanel.vue           # Vista/panel (puede ser sidebar o vista)
│       │   ├── stores/
│       │   │   └── useControlsStore.ts     # Estado: ultimo comando enviado, historial manual
│       │   ├── services/
│       │   │   └── commandService.ts       # POST /api/command/{cmd}
│       │   └── components/
│       │       ├── CommandButton.vue        # Boton individual con icono y estado
│       │       ├── CommandGrid.vue          # Grid de botones (simples + compuestos)
│       │       └── ThresholdSlider.vue      # Ajuste de umbral de confianza
│       │
│       └── system/                         # Feature: estado del sistema
│           ├── SystemView.vue              # Vista de metricas detalladas (ruta /system)
│           ├── stores/
│           │   └── useSystemStore.ts       # Estado: conexion Arduino, modelos, metricas
│           ├── services/
│           │   ├── statusService.ts        # GET /api/status, /api/health
│           │   └── metricsService.ts       # GET /api/metrics
│           └── components/
│               ├── ConnectionStatus.vue     # Estado Arduino + modelos + WebSocket
│               ├── MetricCard.vue           # Tarjeta con metrica individual (override de base)
│               └── MetricsSummary.vue       # Resumen de metricas agregadas
│
├── Dockerfile
├── nginx.conf
└── .dockerignore
```

## Reglas de Arquitectura

### 1. Direccion de dependencias (la regla mas importante)

```
features/ ──imports──▶ core/
core/     ──imports──▶ (nada interno)

features/ ──NUNCA──▶ otra feature/
core/     ──NUNCA──▶ features/
```

- `core/` es la capa de infraestructura. No sabe que features existen.
- Cada `feature/` es un modulo vertical autocontenido (store + service + components + composables).
- Si dos features necesitan compartir algo, ese algo sube a `core/`.

### 2. Design System con tokens

Los **design tokens** son la fuente unica de verdad para toda decision visual:

```ts
// core/design-system/tokens/colors.ts
export const colors = {
  bg:      { primary: '#0f172a', card: '#1e293b', cardHover: '#334155' },
  text:    { primary: '#f1f5f9', secondary: '#94a3b8', muted: '#64748b' },
  accent:  { default: '#38bdf8', hover: '#7dd3fc', glow: 'rgba(56,189,248,0.3)' },
  success: { default: '#4ade80', glow: 'rgba(74,222,128,0.5)' },
  danger:  { default: '#f87171', glow: 'rgba(248,113,113,0.5)' },
  warning: { default: '#fbbf24' },
  command: {
    enciende: '#4ade80', apaga: '#f87171', izquierda: '#38bdf8',
    derecha: '#818cf8', detente: '#fbbf24', enciende_rapido: '#34d399',
    enciende_lento: '#2dd4bf', gira_izquierda: '#60a5fa', gira_derecha: '#a78bfa',
  },
} as const
```

- Tailwind se configura a partir de estos tokens (`tailwind.config.ts` importa de `tokens/`).
- Los componentes base (`BaseButton`, `BaseCard`, etc.) consumen tokens via clases Tailwind o CSS variables.
- Cambiar la paleta completa = editar UN archivo.

### 3. Componentes base vs componentes de feature

| Base (`core/design-system/components/`) | Feature (`features/*/components/`) |
|---|---|
| No tienen logica de negocio | Conocen el dominio (comandos, predicciones) |
| Reciben datos via props | Consumen stores directamente |
| Reutilizables en cualquier contexto | Especificos de su feature |
| Nombrados con prefijo `Base` | Nombrados por lo que hacen |
| Ejemplo: `BaseCard`, `BaseButton` | Ejemplo: `CommandDisplay`, `LatencyChart` |

### 4. Composition API exclusivamente

- Todos los componentes usan `<script setup lang="ts">`.
- No Options API.
- Logica reutilizable se extrae a `composables/` (en `core/` si es generica, en `feature/` si es especifica).

### 5. Tipado estricto con TypeScript

- `tsconfig.json` con `strict: true`.
- Tipos de la API del backend en `core/types/` (compartidos).
- Cada feature puede tener tipos locales si son especificos de su dominio.
- Nunca usar `any`. Preferir `unknown` + type narrowing.

### 6. Estado: Pinia stores con scope

- **Global stores** (en `core/`): solo si multiples features los necesitan (ej: tema, usuario).
- **Feature stores** (en `features/*/stores/`): estado local del feature. Es la norma.
- Los stores solo se comunican con services, nunca hacen fetch directo.

### 7. Comunicacion con el Backend

- **WebSocket** (`ws://<host>/ws/inference`): stream en vivo de predicciones.
  ```json
  {
    "command": "enciende",
    "confidence": 0.94,
    "latency_ms": 3.2,
    "rejected": false
  }
  ```
- **REST API**: estado del sistema, comandos manuales, metricas.
- `core/api/httpClient.ts` maneja base URL, errores, y tipos.
- `core/api/wsClient.ts` maneja reconexion automatica.
- En produccion, nginx proxea `/api/` y `/ws/` al backend.

### 8. Sin dependencias externas en runtime

- No CDNs. Todo bundleado con Vite.
- Compatible con modo avion (una vez cargado).
- Chart.js se importa como dependencia de npm, no desde CDN.

### 9. Responsividad

- Disenar primero para **1920x1080** (proyector de la defensa).
- Tailwind breakpoints para soporte de pantallas menores.
- El layout principal usa CSS Grid con areas nombradas.

### 10. Convenciones de nombrado

| Tipo | Convencion | Ejemplo |
|---|---|---|
| Componentes | PascalCase, prefijo `Base` para design system | `BaseButton.vue`, `CommandDisplay.vue` |
| Composables | camelCase con prefijo `use` | `useWebSocket.ts`, `useInferenceStream.ts` |
| Stores | camelCase con prefijo `use` + sufijo `Store` | `useDashboardStore.ts` |
| Services | camelCase con sufijo `Service` | `commandService.ts` |
| Tokens | camelCase, exportados como `const` objetos | `colors`, `spacing` |
| Tipos | PascalCase | `InferenceEvent`, `CommandType` |

## Comandos del Panel

Los 9 botones manuales del panel domotico:

| Comando | Tipo | Byte | Accion Arduino |
|---|---|---|---|
| enciende | Simple | `0x01` | Cierra rele |
| apaga | Simple | `0x02` | Abre rele |
| izquierda | Simple | `0x03` | Motor pasos 512 antihorario |
| derecha | Simple | `0x04` | Motor pasos 512 horario |
| detente | Simple | `0x05` | Beep 200ms + todo apagado |
| enciende_rapido | Compuesto | `0x10` | Rele ON + LED RGB blanco |
| enciende_lento | Compuesto | `0x11` | Rele ON + LED RGB azul tenue |
| gira_izquierda | Compuesto | `0x12` | Motor 1024 antihorario |
| gira_derecha | Compuesto | `0x13` | Motor 1024 horario |
