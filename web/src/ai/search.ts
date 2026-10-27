import { checkersLeft, type Board, type Move } from '../game/rules'
import type { Evaluator } from './evaluators'
import { allRolls, fullMoves } from './moveGen'

// How many of the best 1-ply candidates are checked with the deeper search
export const CANDIDATES = 8

/** Winning probability of every board from the point of view of player */
export function valuesFor(boards: Board[], player: number, playerToMove: number, evaluator: Evaluator): number[] {
  const values = evaluator.evaluate(boards, playerToMove)
  return boards.map((board, i) => {
    let value = values[i]
    if (checkersLeft(board, 1) === 0) value = 1.0
    else if (checkersLeft(board, -1) === 0) value = 0.0
    return player === 1 ? value : 1 - value
  })
}

/** The average over all the opponent rolls of the position after its best reply,
 * or null when the deadline (a performance.now() time) passed before the calculation ended */
export function expectedAfterReply(board: Board, player: number, evaluator: Evaluator,
                                   deadline: number | null): number | null {
  if (checkersLeft(board, player) === 0) return 1.0
  const opponent = -player
  let total = 0.0
  for (const [dice, probability] of allRolls()) {
    if (deadline !== null && performance.now() > deadline) return null
    const replies = fullMoves(board, opponent, dice).map((option) => option.board)
    total += probability * Math.min(...valuesFor(replies, player, player, evaluator))
  }
  return total
}

export interface SearchOptions {
  depth?: number
  deadline?: number | null
  temperature?: number
  random?: () => number
}

/** The steps of the move to play, an empty list when there is no legal move.
 * depth 2 looks at every opponent roll, and stops at the deadline keeping the 1-ply choice
 * for the candidates it did not reach. temperature above 0 adds randomness for easier play. */
export function chooseMove(board: Board, player: number, dice: number[], evaluator: Evaluator,
                           { depth = 1, deadline = null, temperature = 0, random = Math.random }: SearchOptions = {}): Move[] {
  const options = fullMoves(board, player, dice)
  if (options.length === 1) return options[0].steps

  const scores = valuesFor(options.map((option) => option.board), player, -player, evaluator)
  const order = options.map((_, i) => i).sort((a, b) => scores[b] - scores[a])

  if (temperature > 0) {
    const weights = scores.map((score) => Math.exp((score - scores[order[0]]) / temperature))
    let pick = random() * weights.reduce((sum, w) => sum + w, 0)
    for (let i = 0; i < options.length; i++) {
      pick -= weights[i]
      if (pick < 0) return options[i].steps
    }
    return options[options.length - 1].steps
  }

  let best = order[0]
  if (depth >= 2) {
    let bestScore: number | null = null
    for (const i of order.slice(0, CANDIDATES)) {
      const score = expectedAfterReply(options[i].board, player, evaluator, deadline)
      if (score === null) break
      if (bestScore === null || score > bestScore) {
        best = i
        bestScore = score
      }
    }
  }
  return options[best].steps
}
