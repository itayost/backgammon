/** The setup chosen on the New game screen. A port of game/config.py. */
import type { Player } from './rules'

export const LEVELS = ['easy', 'medium', 'hard'] as const
export type Level = (typeof LEVELS)[number]
export type Opponent = 'computer' | 'friend' | 'self_play'
export type ColorChoice = 'white' | 'black' | 'random'
/** Which players the computer plays, and at what level */
export type ComputerLevels = Partial<Record<Player, Level>>

export const COLOR_NAMES: Record<Player, string> = { 1: 'White', [-1]: 'Black' }

/** color is the human's color; with a friend it is player 1's color */
export interface GameConfig {
  opponent: Opponent
  level: Level
  color: ColorChoice
}

export const DEFAULT_CONFIG: GameConfig = { opponent: 'computer', level: 'medium', color: 'white' }

/** The human's color as 1 or -1, a random color is drawn again for every game */
export function resolveColor(config: GameConfig, random: () => number = Math.random): Player {
  if (config.color === 'random') return random() < 0.5 ? 1 : -1
  return config.color === 'white' ? 1 : -1
}

/** Maps every player the computer plays to its level for one game */
export function computerLevels(config: GameConfig, random: () => number = Math.random): ComputerLevels {
  if (config.opponent === 'friend') return {}
  if (config.opponent === 'self_play') return { 1: config.level, [-1]: config.level }
  return { [-resolveColor(config, random)]: config.level }
}

export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1)
}
