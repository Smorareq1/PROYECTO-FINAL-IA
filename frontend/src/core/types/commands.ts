export const SIMPLE_COMMANDS = ['enciende', 'apaga', 'izquierda', 'derecha', 'detente'] as const
export const COMPOUND_COMMANDS = ['enciende_rapido', 'enciende_lento', 'gira_izquierda', 'gira_derecha'] as const
export const ALL_COMMANDS = [...SIMPLE_COMMANDS, ...COMPOUND_COMMANDS] as const

export type SimpleCommand = typeof SIMPLE_COMMANDS[number]
export type CompoundCommand = typeof COMPOUND_COMMANDS[number]
export type Command = typeof ALL_COMMANDS[number]

export type CommandType = 'simple' | 'compound'

export interface CommandMeta {
  name: Command
  label: string
  type: CommandType
  byte: number
}

export const COMMAND_META: CommandMeta[] = [
  { name: 'enciende',         label: 'Enciende',        type: 'simple',   byte: 0x01 },
  { name: 'apaga',            label: 'Apaga',           type: 'simple',   byte: 0x02 },
  { name: 'izquierda',        label: 'Izquierda',       type: 'simple',   byte: 0x03 },
  { name: 'derecha',          label: 'Derecha',         type: 'simple',   byte: 0x04 },
  { name: 'detente',          label: 'Detente',         type: 'simple',   byte: 0x05 },
  { name: 'enciende_rapido',  label: 'Enc. Rapido',     type: 'compound', byte: 0x10 },
  { name: 'enciende_lento',   label: 'Enc. Lento',      type: 'compound', byte: 0x11 },
  { name: 'gira_izquierda',   label: 'Gira Izq.',       type: 'compound', byte: 0x12 },
  { name: 'gira_derecha',     label: 'Gira Der.',       type: 'compound', byte: 0x13 },
]

export function isCompound(cmd: Command): boolean {
  return (COMPOUND_COMMANDS as readonly string[]).includes(cmd)
}
