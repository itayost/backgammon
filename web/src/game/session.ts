/**
 * One game of backgammon as a turn state machine, without any UI. A port of game/session.py.
 *
 * The players roll, move one die at a time, may undo moves inside their turn, and end the turn
 * with endTurn(). Listeners get every change as an event and read the state from the session.
 */
import {
  applyMove, barOf, checkersLeft, copyBoard, initBoard, mathRng, possibleMoves, rollDice, sameMove,
  type Board, type Move, type Player, type Rng,
} from './rules'

export type Phase = 'await_roll' | 'moving' | 'ready_to_end' | 'game_over'

export const NO_LEGAL_MOVES = 'no legal moves'

export type SessionEvent =
  | { type: 'game_started' }
  | { type: 'rolled'; player: Player; dice: number[] }
  | { type: 'turn_changed' }
  | { type: 'stepped'; player: Player; start: number; end: number | null; hit: boolean }
  | { type: 'undone' }
  | { type: 'turn_started'; player: Player }
  | { type: 'game_over'; winner: Player }

export type Listener = (event: SessionEvent) => void

export interface GameStats {
  turns: number
  hits: Record<Player, number>
  winner: Player | null
  resigned: boolean
}

function newStats(): GameStats {
  return { turns: 0, hits: { 1: 0, [-1]: 0 }, winner: null, resigned: false }
}

interface Snapshot {
  board: Board
  diceLeft: number[]
  hits: Record<Player, number>
}

export class GameSession {
  rng: Rng
  board: Board = initBoard()
  player: Player = 1
  phase: Phase = 'game_over'
  dice: number[] = []
  diceLeft: number[] = []
  legal: Move[] = []
  reason: string | null = null
  /** The opening roll (white die, black die) until the first player's turn ends */
  opening: [number, number] | null = null
  history: Snapshot[] = []
  stats: GameStats = newStats()
  private listeners: Listener[] = []

  constructor(rng: Rng = mathRng) {
    this.rng = rng
  }

  addListener(listener: Listener) {
    this.listeners.push(listener)
  }

  removeListener(listener: Listener) {
    this.listeners = this.listeners.filter((l) => l !== listener)
  }

  private emit(event: SessionEvent) {
    for (const listener of [...this.listeners]) listener(event)
  }

  // Game flow

  /** Starts a new game with the opening roll: each side rolls one die, ties roll again,
   * and the higher die moves first using both dice. opening = [white die, black die] fixes it. */
  start(opening?: [number, number]) {
    this.board = initBoard()
    this.stats = newStats()
    let white: number, black: number
    if (opening === undefined) {
      do {
        white = this.die()
        black = this.die()
      } while (white === black)
    } else {
      [white, black] = opening
    }
    this.opening = [white, black]
    this.player = white > black ? 1 : -1
    this.phase = 'await_roll'
    this.dice = []
    this.diceLeft = []
    this.legal = []
    this.history = []
    this.reason = null
    this.emit({ type: 'game_started' })
    this.beginMoves([white, black])
  }

  roll(dice?: number[]): boolean {
    if (this.phase !== 'await_roll') return false
    const rolled = dice !== undefined ? [...dice] : rollDice(this.rng)
    this.opening = null
    this.emit({ type: 'rolled', player: this.player, dice: [...rolled] })
    this.beginMoves(rolled)
    return true
  }

  private beginMoves(dice: number[]) {
    this.dice = [...dice]
    this.diceLeft = [...dice]
    this.history = []
    this.refreshLegal()
    this.emit({ type: 'turn_changed' })
  }

  /** Plays one die, returns false when the move is not legal now */
  move(position: number, jump: number): boolean {
    if (this.phase !== 'moving' || !this.legal.some((m) => sameMove(m, [position, jump]))) return false
    this.history.push({ board: copyBoard(this.board), diceLeft: [...this.diceLeft], hits: { ...this.stats.hits } })
    const { movesMade, thrown } = applyMove(this.board, this.player, position, jump)
    this.diceLeft.splice(this.diceLeft.indexOf(jump), 1)
    const hit = movesMade.length === 2
    if (hit) this.stats.hits[this.player] += 1
    const end = thrown ? null : movesMade[movesMade.length - 1][1]
    this.emit({ type: 'stepped', player: this.player, start: position, end, hit })
    if (thrown && checkersLeft(this.board, this.player) === 0) {
      this.finish(this.player)
      return true
    }
    this.refreshLegal()
    this.emit({ type: 'turn_changed' })
    return true
  }

  undo(): boolean {
    if ((this.phase !== 'moving' && this.phase !== 'ready_to_end') || this.history.length === 0) return false
    const snapshot = this.history.pop()!
    this.board = snapshot.board
    this.diceLeft = snapshot.diceLeft
    this.stats.hits = snapshot.hits
    this.refreshLegal()
    this.emit({ type: 'undone' })
    this.emit({ type: 'turn_changed' })
    return true
  }

  endTurn(): boolean {
    if (this.phase !== 'ready_to_end') return false
    this.stats.turns += 1
    this.player = -this.player as Player
    this.phase = 'await_roll'
    this.dice = []
    this.diceLeft = []
    this.legal = []
    this.reason = null
    this.history = []
    this.opening = null
    this.emit({ type: 'turn_started', player: this.player })
    return true
  }

  resign(player: Player): boolean {
    if (this.phase === 'game_over') return false
    this.stats.resigned = true
    this.finish(-player as Player)
    return true
  }

  private finish(winner: Player) {
    this.stats.winner = winner
    this.phase = 'game_over'
    this.legal = []
    this.emit({ type: 'game_over', winner })
  }

  // Helpers

  private die(): number {
    return this.rng.randint(1, 6)
  }

  private refreshLegal() {
    this.legal = this.diceLeft.length ? possibleMoves(this.board, this.player, this.diceLeft) : []
    if (this.legal.length) {
      this.phase = 'moving'
      this.reason = null
    } else {
      this.phase = 'ready_to_end'
      // Nothing was played this turn although dice were rolled: say why the turn passes
      this.reason = this.history.length === 0 ? NO_LEGAL_MOVES : null
    }
  }

  isOver(): boolean {
    return this.phase === 'game_over'
  }

  canUndo(): boolean {
    return this.history.length > 0 && (this.phase === 'moving' || this.phase === 'ready_to_end')
  }

  pips(player: Player): number {
    let total = 0
    this.board.forEach(([count, owner], index) => {
      if (count && owner === player) {
        const distance = index === barOf(player) ? 25 : player === 1 ? 25 - index : index
        total += count * distance
      }
    })
    return total
  }

  /** Where a move lands, null when it bears the checker off */
  destination(position: number, jump: number): number | null {
    const end = position + jump * this.player
    return end >= 1 && end <= 24 ? end : null
  }
}
