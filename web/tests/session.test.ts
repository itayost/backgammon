import { beforeEach, describe, expect, test } from 'vitest'
import { checkersLeft, initBoard, type Board, type Player } from '../src/game/rules'
import { GameSession, NO_LEGAL_MOVES, type SessionEvent } from '../src/game/session'
import { emptyBoard, pick, seeded, seededRng, sequenceRng } from './helpers'

describe('GameSession', () => {
  let session: GameSession
  let events: SessionEvent[]

  beforeEach(() => {
    session = new GameSession(seededRng(1))
    events = []
    session.addListener((event) => events.push(event))
  })

  /** Puts the session at the start of a turn on a custom board */
  function atRoll(board: Board, player: Player) {
    session.board = board
    session.player = player
    session.phase = 'await_roll'
  }

  test('the opening roll starts the higher die', () => {
    session.start([3, 5])
    expect(session.player).toBe(-1)
    expect(session.dice).toEqual([3, 5])
    expect(session.phase).toBe('moving')
    expect(session.opening).toEqual([3, 5])
  })

  test('the opening roll repeats ties', () => {
    const tied = new GameSession(sequenceRng([4, 4, 2, 2, 6, 1]))
    tied.start()
    expect(tied.opening).toEqual([6, 1])
    expect(tied.player).toBe(1)
  })

  test('roll only when waiting', () => {
    session.start([6, 1])
    expect(session.roll([3, 4])).toBe(false)
  })

  test('an illegal move is rejected', () => {
    session.start([6, 1])
    expect(session.move(1, 4)).toBe(false)
    expect(session.move(6, 1)).toBe(false)
  })

  test('the turn needs Done', () => {
    session.start([3, 1])
    expect(session.move(17, 3)).toBe(true)
    expect(session.move(19, 1)).toBe(true)
    expect(session.phase).toBe('ready_to_end')
    expect(session.reason).toBeNull()
    expect(session.player).toBe(1)
    expect(session.endTurn()).toBe(true)
    expect(session.player).toBe(-1)
    expect(session.phase).toBe('await_roll')
    expect(session.stats.turns).toBe(1)
    expect(events[events.length - 1]).toEqual({ type: 'turn_started', player: -1 })
  })

  test('end the turn only when ready', () => {
    session.start([3, 1])
    expect(session.endTurn()).toBe(false)
  })

  test('undo restores a hit', () => {
    const board = emptyBoard()
    board[1] = [2, 1]
    board[4] = [1, -1]
    board[20] = [2, -1]
    atRoll(board, 1)
    session.roll([3, 6])
    expect(session.move(1, 3)).toBe(true)
    expect(session.board[25]).toEqual([1, -1])
    expect(session.stats.hits[1]).toBe(1)
    expect(session.undo()).toBe(true)
    expect(session.board[4]).toEqual([1, -1])
    expect(session.board[25][0]).toBe(0)
    expect(session.stats.hits[1]).toBe(0)
    expect([...session.diceLeft].sort()).toEqual([3, 6])
    expect(session.phase).toBe('moving')
  })

  test('undo from ready, and nothing to undo', () => {
    session.start([3, 1])
    expect(session.undo()).toBe(false)
    session.move(17, 3)
    session.move(19, 1)
    expect(session.undo()).toBe(true)
    expect(session.phase).toBe('moving')
    expect(session.diceLeft).toEqual([1])
  })

  test('no legal moves waits for Done', () => {
    const board = emptyBoard()
    board[0] = [1, 1]
    for (let i = 1; i <= 6; i++) board[i] = [2, -1]
    board[24] = [14, 1]
    atRoll(board, 1)
    session.roll([3, 4])
    expect(session.phase).toBe('ready_to_end')
    expect(session.reason).toBe(NO_LEGAL_MOVES)
    expect(session.endTurn()).toBe(true)
    expect(session.player).toBe(-1)
  })

  test('a checker on the bar must enter first', () => {
    const board = initBoard()
    board[0] = [1, 1]
    board[1] = [1, 1]
    atRoll(board, 1)
    session.roll([3, 5])
    expect(session.legal.every(([position]) => position === 0)).toBe(true)
  })

  test('white wins by bearing off', () => {
    const board = emptyBoard()
    board[24] = [1, 1]
    board[5] = [3, -1]
    atRoll(board, 1)
    session.roll([6, 3])
    expect(session.move(24, 6)).toBe(true)
    expect(session.phase).toBe('game_over')
    expect(session.stats.winner).toBe(1)
    expect(events[events.length - 1]).toEqual({ type: 'game_over', winner: 1 })
  })

  test('black wins by bearing off', () => {
    const board = emptyBoard()
    board[2] = [1, -1]
    board[20] = [3, 1]
    atRoll(board, -1)
    session.roll([2, 1])
    expect(session.move(2, 2)).toBe(true)
    expect(session.stats.winner).toBe(-1)
    expect(session.undo()).toBe(false)
  })

  test('resign', () => {
    session.start([3, 1])
    expect(session.resign(1)).toBe(true)
    expect(session.stats.winner).toBe(-1)
    expect(session.stats.resigned).toBe(true)
    expect(session.resign(1)).toBe(false)
  })

  test('pips at the start', () => {
    session.start([3, 1])
    expect(session.pips(1)).toBe(167)
    expect(session.pips(-1)).toBe(167)
  })

  test('the events of a move', () => {
    session.start([3, 1])
    events.length = 0
    session.move(17, 3)
    expect(events.map((event) => event.type)).toEqual(['stepped', 'turn_changed'])
    expect(events[0]).toEqual({ type: 'stepped', player: 1, start: 17, end: 20, hit: false })
  })

  test('random games finish with legal states', () => {
    const random = seeded(3)
    for (let game = 0; game < 20; game++) {
      session.start()
      while (session.phase !== 'game_over') {
        if (session.phase === 'await_roll') session.roll()
        else if (session.phase === 'moving') {
          if (random() < 0.1 && session.canUndo()) session.undo()
          else {
            const [position, jump] = pick(random, session.legal)
            session.move(position, jump)
          }
        } else session.endTurn()
        for (const [count, owner] of session.board) {
          expect(count).toBeGreaterThanOrEqual(0)
          if (count) expect([1, -1]).toContain(owner)
        }
        for (const player of [1, -1]) expect(checkersLeft(session.board, player)).toBeLessThanOrEqual(15)
      }
      expect(checkersLeft(session.board, session.stats.winner!)).toBe(0)
    }
  })
})
