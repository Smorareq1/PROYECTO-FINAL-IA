export const colors = {
  bg: {
    primary: '#ffffff',
    surface: '#fafafa',
    surfaceAlt: '#f4f4f4',
    inverse: '#0a0a0a',
    overlay: 'rgba(10, 10, 10, 0.6)',
  },
  text: {
    primary: '#0a0a0a',
    secondary: '#525252',
    muted: '#a3a3a3',
    onInverse: '#fafafa',
  },
  border: {
    subtle: '#ececec',
    default: '#e5e5e5',
    strong: '#0a0a0a',
  },
  accent: {
    default: '#e63946',
    hover: '#c2303c',
    soft: '#fde7e9',
  },
  success: {
    default: '#1f7a4d',
    soft: '#e3f1ea',
  },
  danger: {
    default: '#c1121f',
    soft: '#fde7e9',
  },
  warning: {
    default: '#b8860b',
    soft: '#fbf1d9',
  },
  info: {
    default: '#1d3557',
    soft: '#e4ebf3',
  },
  command: {
    enciende:        '#1f7a4d',
    apaga:           '#c1121f',
    izquierda:       '#1d3557',
    derecha:         '#6f4e37',
    detente:         '#b8860b',
    enciende_rapido: '#2a9d8f',
    enciende_lento:  '#457b9d',
    gira_izquierda:  '#264653',
    gira_derecha:    '#774936',
  },
} as const

export type CommandColor = keyof typeof colors.command
