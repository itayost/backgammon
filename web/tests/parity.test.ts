/** The TypeScript port must say exactly what the Python code says about the same positions.
 * The fixtures come from web/scripts/make_fixtures.py. */
import { describe, expect, test } from 'vitest'
import { HeuristicEvaluator } from '../src/ai/evaluators'
import { fullMoves } from '../src/ai/moveGen'
import { loadEvaluator } from '../src/ai/player'
import { chooseMove } from '../src/ai/search'
import { copyBoard, possibleMoves, type Board, type Move } from '../src/game/rules'
import fixtures from './fixtures/parity.json'

interface Fixture {
  board: Board
  player: number
  dice: number[]
  legal: Move[]
  full: Move[][]
  heuristic: [number, number]
  td: [number, number]
  medium: Move[]
  hard: Move[] | null
}

const positions = fixtures.positions as unknown as Fixture[]
const heuristic = new HeuristicEvaluator()
const td = loadEvaluator('td')
// Math.exp in JavaScript and the C library may differ in the last bit, nothing more
const TOLERANCE = 1e-12

describe('the port matches the Python code', () => {
  test('there are positions to compare', () => {
    expect(positions.length).toBeGreaterThan(300)
  })

  test('legal moves, in the same order', () => {
    for (const p of positions) expect(possibleMoves(p.board, p.player, p.dice)).toEqual(p.legal)
  })

  test('every reachable position, found with the same steps in the same order', () => {
    for (const p of positions) {
      const before = copyBoard(p.board)
      expect(fullMoves(p.board, p.player, p.dice).map((option) => option.steps)).toEqual(p.full)
      expect(p.board).toEqual(before)
    }
  })

  test('the hand written evaluation', () => {
    for (const p of positions) {
      expect(Math.abs(heuristic.evaluateOne(p.board, 1) - p.heuristic[0])).toBeLessThan(TOLERANCE)
      expect(Math.abs(heuristic.evaluateOne(p.board, -1) - p.heuristic[1])).toBeLessThan(TOLERANCE)
    }
  })

  test('the trained network', () => {
    for (const p of positions) {
      expect(Math.abs(td.evaluate([p.board], 1)[0] - p.td[0])).toBeLessThan(TOLERANCE)
      expect(Math.abs(td.evaluate([p.board], -1)[0] - p.td[1])).toBeLessThan(TOLERANCE)
    }
  })

  test('the move medium chooses', () => {
    for (const p of positions) expect(chooseMove(p.board, p.player, p.dice, heuristic)).toEqual(p.medium)
  })

  test('the move the 2-ply search with the network chooses', () => {
    const checked = positions.filter((p) => p.hard !== null)
    expect(checked.length).toBeGreaterThan(50)
    for (const p of checked) expect(chooseMove(p.board, p.player, p.dice, td, { depth: 2 })).toEqual(p.hard)
  }, 60_000)
})
