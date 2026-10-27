/** A TD-Gammon style network: the board encoding of Tesauro, one hidden layer and the probability that
 * white wins. A port of the evaluation in ai/td.py; training stays in Python (ai/train_td.py) and
 * web/scripts/export_weights.py writes the trained weights to weights/td.json. */
import { BLACK_BAR, CHECKERS_PER_PLAYER, WHITE_BAR, borneOff, type Board } from '../game/rules'
import type { Evaluator } from './evaluators'

export const INPUTS = 198

export interface Weights {
  hidden: number
  inputs: number
  /** Row major, w1[j * inputs + k] */
  w1: number[]
  b1: number[]
  w2: number[]
  b2: number
}

export function encode(board: Board, playerToMove: number): Float64Array {
  const x = new Float64Array(INPUTS)
  let i = 0
  for (const side of [1, -1]) {
    for (let point = 1; point <= 24; point++) {
      const n = board[point][1] === side ? board[point][0] : 0
      x[i] = n >= 1 ? 1 : 0
      x[i + 1] = n >= 2 ? 1 : 0
      x[i + 2] = n >= 3 ? 1 : 0
      x[i + 3] = Math.max(n - 3, 0) / 2
      i += 4
    }
  }
  x[192] = board[WHITE_BAR][0] / 2
  x[193] = board[BLACK_BAR][0] / 2
  x[194] = borneOff(board, 1) / CHECKERS_PER_PLAYER
  x[195] = borneOff(board, -1) / CHECKERS_PER_PLAYER
  x[196] = playerToMove === 1 ? 1 : 0
  x[197] = playerToMove === -1 ? 1 : 0
  return x
}

function sigmoid(z: number): number {
  return 1 / (1 + Math.exp(-z))
}

export class TDEvaluator implements Evaluator {
  private w1: Float64Array
  private hiddenValues: Float64Array

  constructor(private weights: Weights) {
    this.w1 = Float64Array.from(weights.w1)
    this.hiddenValues = new Float64Array(weights.hidden)
  }

  evaluate(boards: Board[], playerToMove: number): number[] {
    return boards.map((board) => this.value(encode(board, playerToMove)))
  }

  value(x: Float64Array): number {
    const { hidden, inputs, b1, w2, b2 } = this.weights
    const h = this.hiddenValues
    for (let j = 0; j < hidden; j++) {
      let sum = 0
      const row = j * inputs
      for (let k = 0; k < inputs; k++) {
        if (x[k] !== 0) sum += this.w1[row + k] * x[k]
      }
      h[j] = sigmoid(sum + b1[j])
    }
    let out = 0
    for (let j = 0; j < hidden; j++) out += h[j] * w2[j]
    return sigmoid(out + b2)
  }
}
