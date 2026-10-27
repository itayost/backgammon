import type { Level } from '../game/config'
import type { Board, Move } from '../game/rules'
import { HeuristicEvaluator, type Evaluator } from './evaluators'
import { chooseMove } from './search'
import { TDEvaluator, type Weights } from './td'
import tdWeights from './weights/td.json'

interface LevelSettings {
  depth: number
  temperature: number
  /** Seconds the deeper search may take, null for no limit */
  timeLimit: number | null
  evaluator: 'heuristic' | 'td'
}

// Looking at the opponent's replies (depth 2) only made the computer stronger with the trained network,
// with the hand written evaluation it played as well as depth 1, so hard uses the network.
export const LEVEL_SETTINGS: Record<Level, LevelSettings> = {
  easy: { depth: 1, temperature: 0.05, timeLimit: null, evaluator: 'heuristic' },
  medium: { depth: 1, temperature: 0.0, timeLimit: null, evaluator: 'heuristic' },
  hard: { depth: 2, temperature: 0.0, timeLimit: 2.5, evaluator: 'td' },
}

export function loadEvaluator(name: LevelSettings['evaluator']): Evaluator {
  return name === 'td' ? new TDEvaluator(tdWeights as Weights) : new HeuristicEvaluator()
}

export class ComputerPlayer {
  readonly settings: LevelSettings
  readonly evaluator: Evaluator

  constructor(readonly level: Level, evaluator?: Evaluator, private random: () => number = Math.random) {
    this.settings = LEVEL_SETTINGS[level]
    this.evaluator = evaluator ?? loadEvaluator(this.settings.evaluator)
  }

  /** The steps (position, jump) to play for this roll */
  choose(board: Board, player: number, dice: number[]): Move[] {
    const limit = this.settings.timeLimit
    const deadline = limit !== null ? performance.now() + limit * 1000 : null
    return chooseMove(board, player, dice, this.evaluator, {
      depth: this.settings.depth, deadline, temperature: this.settings.temperature, random: this.random,
    })
  }
}
