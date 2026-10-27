import { describe, expect, test } from 'vitest'
import { HeuristicEvaluator } from '../src/ai/evaluators'
import { allRolls, boardKey, fullMoves } from '../src/ai/moveGen'
import { ComputerPlayer } from '../src/ai/player'
import { chooseMove } from '../src/ai/search'
import { TDEvaluator } from '../src/ai/td'
import { LEVELS } from '../src/game/config'
import { applyMove, checkersLeft, copyBoard, initBoard, possibleMoves, rollDice } from '../src/game/rules'
import { emptyBoard, pick, play, seeded, seededRng } from './helpers'

describe('move generation', () => {
  test('the rolls cover all the probability', () => {
    const rolls = allRolls()
    expect(rolls).toHaveLength(21)
    expect(rolls.reduce((sum, [, p]) => sum + p, 0)).toBeCloseTo(1.0, 12)
  })

  test('full moves are legal and distinct', () => {
    const random = seeded(1)
    const rng = seededRng(2)
    let board = initBoard()
    let player = 1
    for (let turn = 0; turn < 40; turn++) {
      const dice = rollDice(rng)
      const options = fullMoves(board, player, dice)
      const keys = options.map((option) => boardKey(option.board))
      expect(new Set(keys).size).toBe(keys.length)
      for (const option of options) {
        const [played, left] = play(board, player, dice, option.steps)
        expect(boardKey(played)).toBe(boardKey(option.board))
        if (checkersLeft(played, player)) expect(possibleMoves(played, player, left)).toEqual([])
      }
      board = pick(random, options).board
      if (checkersLeft(board, player) === 0) break
      player = -player
    }
  })

  test('no moves keeps the board', () => {
    const board = emptyBoard()
    board[0] = [1, 1]
    for (let i = 1; i <= 6; i++) board[i] = [2, -1]
    const options = fullMoves(board, 1, [3, 4])
    expect(options).toHaveLength(1)
    expect(options[0].steps).toEqual([])
  })

  test('does not change the input board', () => {
    const board = initBoard()
    fullMoves(board, 1, [6, 6, 6, 6])
    expect(board).toEqual(initBoard())
  })
})

describe('evaluation', () => {
  test('the race leader is the favourite', () => {
    const board = emptyBoard()
    board[22] = [15, 1]
    board[10] = [15, -1]
    expect(new HeuristicEvaluator().evaluateOne(board, 1)).toBeGreaterThan(0.9)
  })

  test('a blot in front of the opponent is worse', () => {
    const safe = initBoard()
    const exposed = copyBoard(safe)
    applyMove(exposed, 1, 1, 4) // white leaves a blot on 1 and on 5, in front of black's 6 and 8
    const evaluator = new HeuristicEvaluator()
    expect(evaluator.evaluateOne(exposed, -1)).toBeLessThan(evaluator.evaluateOne(safe, -1))
  })

  test('the network scores are probabilities', () => {
    const value = new ComputerPlayer('hard').evaluator.evaluate([initBoard()], 1)[0]
    expect(value).toBeGreaterThanOrEqual(0)
    expect(value).toBeLessThanOrEqual(1)
  })

  test('hard uses the trained network', () => {
    expect(new ComputerPlayer('hard').evaluator).toBeInstanceOf(TDEvaluator)
    expect(new ComputerPlayer('medium').evaluator).toBeInstanceOf(HeuristicEvaluator)
  })
})

describe('search', () => {
  test('hits a free blot', () => {
    const board = emptyBoard()
    board[2] = [1, 1]
    board[19] = [7, 1]
    board[20] = [7, 1]
    board[5] = [1, -1]
    board[3] = [14, -1]
    const steps = chooseMove(board, 1, [3, 1], new HeuristicEvaluator())
    const [result] = play(board, 1, [3, 1], steps)
    expect(result[25][0]).toBe(1)
  })

  test('takes the last checker off when it can', () => {
    const board = emptyBoard()
    board[24] = [1, 1]
    board[5] = [3, -1]
    const steps = chooseMove(board, 1, [6, 1], new HeuristicEvaluator(), { depth: 2 })
    const [result] = play(board, 1, [6, 1], steps)
    expect(checkersLeft(result, 1)).toBe(0)
  })

  test('the deep search respects the deadline', () => {
    const board = initBoard()
    const start = performance.now()
    const steps = chooseMove(board, 1, [3, 3, 3, 3], new HeuristicEvaluator(), { depth: 2, deadline: start + 200 })
    expect(performance.now() - start).toBeLessThan(1000)
    play(board, 1, [3, 3, 3, 3], steps)
  })

  test('every level returns legal moves', () => {
    const random = seeded(2)
    const rng = seededRng(3)
    for (const level of LEVELS) {
      const computer = new ComputerPlayer(level, undefined, seeded(0))
      let board = initBoard()
      let player = 1
      for (let turn = 0; turn < 6; turn++) {
        const dice = rollDice(rng)
        const [after, left] = play(board, player, dice, computer.choose(board, player, dice))
        expect(possibleMoves(after, player, left)).toEqual([])
        board = pick(random, fullMoves(after, -player, rollDice(rng))).board
      }
    }
  })
})

describe('strength', () => {
  /** Plays a full game between two choosers, returns the winner */
  function playGame(choosers: Record<number, (board: ReturnType<typeof initBoard>, player: number, dice: number[]) => [number, number][]>,
                    rng: ReturnType<typeof seededRng>, first: number): number {
    let board = initBoard()
    let player = first
    for (;;) {
      const dice = rollDice(rng)
      ;[board] = play(board, player, dice, choosers[player](board, player, dice))
      if (checkersLeft(board, player) === 0) return player
      player = -player
    }
  }

  test('medium beats random play', () => {
    const random = seeded(7)
    const rng = seededRng(8)
    const medium = new ComputerPlayer('medium')
    let wins = 0
    const games = 30
    for (let game = 0; game < games; game++) {
      const side = game % 2 === 0 ? 1 : -1
      const choosers = {
        [side]: (b: ReturnType<typeof initBoard>, p: number, d: number[]) => medium.choose(b, p, d),
        [-side]: (b: ReturnType<typeof initBoard>, p: number, d: number[]) => pick(random, fullMoves(b, p, d)).steps,
      }
      if (playGame(choosers, rng, game % 3 === 0 ? 1 : -1) === side) wins += 1
    }
    expect(wins / games).toBeGreaterThanOrEqual(0.8)
  })
})
