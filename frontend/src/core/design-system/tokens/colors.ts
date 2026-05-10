export const colors = {
  bg: {
    primary: '#0f172a',
    card: '#1e293b',
    cardHover: '#334155',
    overlay: 'rgba(0, 0, 0, 0.5)',
  },
  text: {
    primary: '#f1f5f9',
    secondary: '#94a3b8',
    muted: '#64748b',
  },
  border: {
    default: '#334155',
    hover: '#475569',
  },
  accent: {
    default: '#38bdf8',
    hover: '#7dd3fc',
    glow: 'rgba(56, 189, 248, 0.3)',
  },
  success: {
    default: '#4ade80',
    glow: 'rgba(74, 222, 128, 0.5)',
  },
  danger: {
    default: '#f87171',
    glow: 'rgba(248, 113, 113, 0.5)',
  },
  warning: {
    default: '#fbbf24',
  },
  command: {
    enciende: '#4ade80',
    apaga: '#f87171',
    izquierda: '#38bdf8',
    derecha: '#818cf8',
    detente: '#fbbf24',
    enciende_rapido: '#34d399',
    enciende_lento: '#2dd4bf',
    gira_izquierda: '#60a5fa',
    gira_derecha: '#a78bfa',
  },
} as const

export type CommandColor = keyof typeof colors.command
