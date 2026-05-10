export const typography = {
  fontFamily: {
    sans: "'Segoe UI', system-ui, -apple-system, sans-serif",
    mono: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace",
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.85rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '2rem',
    '4xl': '3.5rem',
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  lineHeight: {
    tight: '1.2',
    normal: '1.5',
    relaxed: '1.6',
  },
  letterSpacing: {
    tight: '-0.01em',
    normal: '0',
    wide: '0.05em',
    wider: '0.1em',
  },
} as const
