import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { AIController } from '../src/ai/controller'
import { ComputerPlayer } from '../src/ai/player'
import type { Thinker } from '../src/ai/thinker'
import type { ComputerLevels, Level } from '../src/game/config'
import type { Board, Move } from '../src/game/rules'
import { GameSession } from '../src/game/session'
import { seeded, seededRng } from './helpers'

/** Thinks on the spot instead of in a worker */
class DirectThinker implements Thinker {
  calls = 0
  cancelled = 0
  private players = new Map<Level, ComputerPlayer>()

  think(level: Level, board: Board, player: number, dice: number[]): Promise<Move[] | null> {
    this.calls += 1
    if (!this.players.has(level)) this.players.set(level, new ComputerPlayer(level, undefined, seeded(this.players.size + 1)))
    return Promise.resolve(this.players.get(level)!.choose(board, player, dice))
  }

  cancel() {
    this.cancelled += 1
  }
}

describe('AIController', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  function controller(session: GameSession, computers: ComputerLevels, thinker: Thinker = new DirectThinker()) {
    return new AIController(session, computers, thinker, { stepDelayMs: 0, rollDelayMs: 0 })
  }

  test('computers play a full game', async () => {
    const session = new GameSession(seededRng(5))
    const ai = controller(session, { 1: 'medium', [-1]: 'easy' })
    session.start()
    for (let tick = 0; tick < 5000 && !session.isOver(); tick++) await vi.advanceTimersByTimeAsync(1)
    ai.stop()
    expect(session.isOver()).toBe(true)
    const winner = session.stats.winner!
    expect(session.board.filter(([, owner]) => owner === winner).reduce((sum, [count]) => sum + count, 0)).toBe(0)
    expect(session.stats.turns).toBeGreaterThan(10)
  })

  test("the human's turn is left alone", async () => {
    const session = new GameSession(seededRng(5))
    const ai = controller(session, { [-1]: 'easy' })
    session.start([6, 1])
    await vi.advanceTimersByTimeAsync(200)
    expect(session.player).toBe(1)
    expect(session.phase).toBe('moving')
    ai.stop()
  })

  test('pause holds and resume continues', async () => {
    const session = new GameSession(seededRng(5))
    const ai = controller(session, { 1: 'easy' })
    ai.pause()
    session.start([6, 1])
    await vi.advanceTimersByTimeAsync(300)
    expect(session.diceLeft).toEqual([6, 1])
    ai.resume()
    for (let tick = 0; tick < 100 && session.player !== -1; tick++) await vi.advanceTimersByTimeAsync(1)
    expect(session.player).toBe(-1)
    ai.stop()
  })

  test('the answer for an old turn is ignored', async () => {
    const session = new GameSession(seededRng(5))
    let answer: (steps: Move[] | null) => void = () => {}
    const slow: Thinker = { think: () => new Promise((resolve) => { answer = resolve }), cancel: () => {} }
    const ai = controller(session, { 1: 'easy' }, slow)
    session.start([6, 1])
    await vi.advanceTimersByTimeAsync(0)
    const late = session.legal[0]
    // A new game starts while the computer still thinks about the old one
    session.start([1, 6])
    answer([late])
    await vi.advanceTimersByTimeAsync(10)
    expect(session.player).toBe(-1)
    expect(session.diceLeft).toEqual([1, 6])
    ai.stop()
  })

  test('a new game cancels the thinking', async () => {
    const session = new GameSession(seededRng(5))
    const thinker = new DirectThinker()
    const ai = controller(session, { 1: 'easy' }, thinker)
    session.start([6, 1])
    const before = thinker.cancelled
    session.start([6, 1])
    expect(thinker.cancelled).toBe(before + 1)
    ai.stop()
  })

  test('a failed choice falls back to a legal move', async () => {
    const session = new GameSession(seededRng(5))
    const failing: Thinker = { think: () => Promise.resolve(null), cancel: () => {} }
    const ai = controller(session, { 1: 'easy' }, failing)
    session.start([6, 1])
    for (let tick = 0; tick < 100 && session.player !== -1; tick++) await vi.advanceTimersByTimeAsync(1)
    expect(session.player).toBe(-1)
    ai.stop()
  })
})
