export const SIMPLE_COMMANDS = ['enciende', 'apaga', 'detente', 'rojo', 'verde', 'azul'] as const
export const COMPOUND_COMMANDS = ['blanco', 'procesando', 'alarma', 'tono'] as const
export const ALL_COMMANDS = [...SIMPLE_COMMANDS, ...COMPOUND_COMMANDS] as const

export type SimpleCommand = typeof SIMPLE_COMMANDS[number]
export type CompoundCommand = typeof COMPOUND_COMMANDS[number]
export type Command = typeof ALL_COMMANDS[number]

export type CommandType = 'simple' | 'compound'

export interface CommandMeta {
  name: Command
  label: string
  type: CommandType
  /** Texto exacto que se envía al Arduino por serial (ASCII + '\n'). */
  serial: string
  /** Color asociado al comando en la UI (hex). */
  color?: string
  /** Descripción de la acción física que ejecuta el Arduino. */
  description: string
}

export const COMMAND_META: CommandMeta[] = [
  // Simples
  { name: 'enciende',   label: 'Enciende',   type: 'simple',   serial: 'enciende',   color: '#facc15', description: 'Relé ON + RGB blanco + beep' },
  { name: 'apaga',      label: 'Apaga',      type: 'simple',   serial: 'apaga',      color: '#64748b', description: 'Relé OFF + RGB off + beep' },
  { name: 'detente',    label: 'Detente',    type: 'simple',   serial: 'detente',    color: '#ef4444', description: 'Apaga todo + beep largo' },
  { name: 'rojo',       label: 'Rojo',       type: 'simple',   serial: 'rojo',       color: '#ef4444', description: 'RGB rojo' },
  { name: 'verde',      label: 'Verde',      type: 'simple',   serial: 'verde',      color: '#22c55e', description: 'RGB verde' },
  { name: 'azul',       label: 'Azul',       type: 'simple',   serial: 'azul',       color: '#3b82f6', description: 'RGB azul' },
  // Compuestos
  { name: 'blanco',     label: 'Blanco',     type: 'compound', serial: 'blanco',     color: '#f8fafc', description: 'RGB blanco brillante' },
  { name: 'procesando', label: 'Procesando', type: 'compound', serial: 'procesando', color: '#f59e0b', description: 'LED amarillo + RGB naranja' },
  { name: 'alarma',     label: 'Alarma',     type: 'compound', serial: 'alarma',     color: '#dc2626', description: '4x parpadeo rojo + buzzer' },
  { name: 'tono',       label: 'Tono',       type: 'compound', serial: 'tono',       color: '#a855f7', description: 'Melodía 3 notas en buzzer' },
]

export function isCompound(cmd: Command): boolean {
  return (COMPOUND_COMMANDS as readonly string[]).includes(cmd)
}
