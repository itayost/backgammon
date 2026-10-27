import type { ComputerLevels } from '../game/config'
import { copyBoard, type Move, type Player } from '../game/rules'
import type { GameSession, SessionEvent } from '../game/session'
import { HeuristicEvaluator } from './evaluators'
import { chooseMove } from './search'
import type { Thinker } from './thinker'

export interface Pacing {
  stepDelayMs?: number
  rollDelayMs?: number
}

/**
 * Plays for the computer players of a GameSession: rolls, thinks with the thinker, plays the chosen
 * steps one by one with a pause between them, and ends the turn. A port of ai/ai_controller.py.
 *
 * Every scheduled action carries the generation it was planned in; a new game, a new turn or
 * the end of the game starts a new generation, so anything planned before is dropped.
 */
export class AIController {
  stepDelayMs: number
  rollDelayMs: number
  private generation = 0
  private paused = false
  private pending: [number, () => void] | null = null
  private steps: Move[] = []
  private timers = new Set<ReturnType<typeof setTimeout>>()

  constructor(private session: GameSession, private computers: ComputerLevels, private thinker: Thinker,
              { stepDelayMs = 500, rollDelayMs = 400 }: Pacing = {}) {
    this.stepDelayMs = stepDelayMs
    this.rollDelayMs = rollDelayMs
    session.addListener(this.onEvent)
  }

  private onEvent = (event: SessionEvent) => {
    if (event.type === 'game_started' || event.type === 'turn_started' || event.type === 'game_over') this.cancel()
    if (event.type === 'game_started' || event.type === 'turn_started') this.later(() => this.check(), 0)
  }

  private cancel() {
    this.generation += 1
    this.steps = []
    this.pending = null
    this.thinker.cancel()
  }

  /** Detaches from the session and drops everything planned */
  stop() {
    this.cancel()
    this.session.removeListener(this.onEvent)
    for (const timer of this.timers) clearTimeout(timer)
    this.timers.clear()
  }

  pause() {
    this.paused = true
  }

  resume() {
    this.paused = false
    if (this.pending !== null) {
      const [generation, action] = this.pending
      this.pending = null
      this.runIfCurrent(generation, action)
    }
  }

  private later(action: () => void, delayMs: number) {
    const generation = this.generation
    const timer = setTimeout(() => {
      this.timers.delete(timer)
      this.runIfCurrent(generation, action)
    }, delayMs)
    this.timers.add(timer)
  }

  private runIfCurrent(generation: number, action: () => void) {
    if (generation !== this.generation) return
    if (this.paused) {
      this.pending = [generation, action]
      return
    }
    action()
  }

  private isComputer(player: Player): boolean {
    return this.computers[player] !== undefined
  }

  /** Does the next thing the computer has to do in its turn */
  private check() {
    const session = this.session
    if (session.phase === 'game_over' || !this.isComputer(session.player)) return
    if (session.phase === 'await_roll') this.later(() => this.roll(), this.rollDelayMs)
    else if (session.phase === 'moving') this.think()
    else if (session.phase === 'ready_to_end') this.later(() => session.endTurn(), this.stepDelayMs)
  }

  private roll() {
    this.session.roll()
    // Leave the dice on screen for a moment before moving
    this.later(() => this.check(), this.rollDelayMs)
  }

  private think() {
    const session = this.session
    const generation = this.generation
    this.thinker.think(this.computers[session.player]!, copyBoard(session.board), session.player,
                       [...session.diceLeft])
      .then((steps) => this.onThought(generation, steps))
  }

  private onThought(generation: number, steps: Move[] | null) {
    if (generation !== this.generation) return
    this.steps = steps !== null ? [...steps] : this.quickSteps()
    this.later(() => this.playStep(), this.stepDelayMs)
  }

  /** A fast choice when the thinking failed, the first legal move if even that fails */
  private quickSteps(): Move[] {
    const session = this.session
    try {
      return chooseMove(session.board, session.player, session.diceLeft, new HeuristicEvaluator())
    } catch (error) {
      console.error('the quick choice failed too', error)
      return session.legal.length ? [session.legal[0]] : []
    }
  }

  private playStep() {
    const session = this.session
    if (session.phase !== 'moving') {
      this.check()
      return
    }
    const generation = this.generation
    const step = this.steps.shift()
    if (step === undefined || !session.move(step[0], step[1])) {
      if (step !== undefined) console.error('the session rejected the computer move', step)
      this.steps = this.quickSteps()
      const retry = this.steps.shift()
      if (retry === undefined || !session.move(retry[0], retry[1])) return
    }
    // Winning the game ends the generation while the move is played
    if (generation !== this.generation || session.isOver()) return
    this.later(this.steps.length ? () => this.playStep() : () => this.check(), this.stepDelayMs)
  }
}
