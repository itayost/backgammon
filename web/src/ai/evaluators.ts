import { barOf, checkersLeft, owns, type Board } from '../game/rules'

export interface Evaluator {
  /** The probability that white wins from each board */
  evaluate(boards: Board[], playerToMove: number): number[]
}

// Number of rolls out of 36 that hit a blot at a given distance from a single shooter (ignoring blocked points)
const SHOTS: Record<number, number> = {
  1: 11, 2: 12, 3: 14, 4: 15, 5: 15, 6: 17, 7: 6, 8: 6, 9: 5, 10: 3, 11: 2, 12: 3,
  15: 1, 16: 1, 18: 1, 20: 1, 24: 1,
}

export function sigmoid(z: number): number {
  return 1 / (1 + Math.exp(-z))
}

/** How far a checker is from bearing off */
export function pip(index: number, player: number): number {
  if (index === barOf(player)) return 25
  return player === 1 ? 25 - index : index
}

interface Features {
  pip: number
  onBoard: number
  homePoints: number
  anchors: number
  prime: number
  bar: number
  risk: number
}

/** Hand written evaluation, a port of HeuristicEvaluator in ai/evaluators.py */
export class HeuristicEvaluator implements Evaluator {
  evaluate(boards: Board[], playerToMove: number): number[] {
    return boards.map((board) => this.evaluateOne(board, playerToMove))
  }

  evaluateOne(board: Board, playerToMove: number): number {
    const white = this.features(board, 1, playerToMove)
    const black = this.features(board, -1, playerToMove)

    if (!HeuristicEvaluator.hasContact(board)) {
      const effectiveWhite = white.pip + 2 * white.onBoard
      const effectiveBlack = black.pip + 2 * black.onBoard
      const diff = effectiveBlack - effectiveWhite + (playerToMove === 1 ? 4 : -4)
      return sigmoid((2.5 * diff) / Math.sqrt((effectiveWhite + effectiveBlack) / 2 + 1))
    }

    let score = 0.03 * (black.pip - white.pip)
    score += 0.2 * (white.homePoints * (1 + 0.5 * black.bar) - black.homePoints * (1 + 0.5 * white.bar))
    score += 0.04 * (white.prime ** 2 - black.prime ** 2)
    score += 0.25 * (Math.min(white.anchors, 2) - Math.min(black.anchors, 2))
    score -= 0.05 * (white.risk - black.risk)
    score -= 0.3 * (white.bar - black.bar)
    score += 0.15 * (black.onBoard - white.onBoard)
    return sigmoid(score)
  }

  static hasContact(board: Board): boolean {
    let lowestWhite = Infinity
    let highestBlack = -Infinity
    for (let i = 0; i < 26; i++) {
      if (owns(board, i, 1)) lowestWhite = Math.min(lowestWhite, i)
      if (owns(board, i, -1)) highestBlack = Math.max(highestBlack, i)
    }
    if (lowestWhite === Infinity || highestBlack === -Infinity) return false
    return lowestWhite < highestBlack
  }

  private features(board: Board, player: number, playerToMove: number): Features {
    const [homeLow, homeHigh] = player === 1 ? [19, 24] : [1, 6]
    const [awayLow, awayHigh] = player === 1 ? [1, 6] : [19, 24]
    const made = board.map(([count, owner], i) => i >= 1 && i <= 24 && owner === player && count >= 2)

    let prime = 0
    let run = 0
    for (let i = 1; i <= 24; i++) {
      run = made[i] ? run + 1 : 0
      prime = Math.max(prime, run)
    }

    let risk = 0
    for (let i = 1; i <= 24; i++) {
      if (board[i][1] === player && board[i][0] === 1) {
        const hit = HeuristicEvaluator.hitProbability(board, i, player)
        const progress = 25 - pip(i, player)
        risk += hit * progress
      }
    }
    // The blots of the player to move are attacked only after its next move
    if (player === playerToMove) risk *= 0.3

    let pips = 0
    let homePoints = 0
    let anchors = 0
    for (let i = 0; i < 26; i++) {
      if (owns(board, i, player)) pips += board[i][0] * pip(i, player)
      if (made[i] && i >= homeLow && i <= homeHigh) homePoints += 1
      if (made[i] && i >= awayLow && i <= awayHigh) anchors += 1
    }

    return {
      pip: pips,
      onBoard: checkersLeft(board, player),
      homePoints,
      anchors,
      prime,
      bar: board[barOf(player)][0],
      risk,
    }
  }

  static hitProbability(board: Board, index: number, player: number): number {
    const opponent = -player
    let miss = 1.0
    for (let j = 0; j < 26; j++) {
      if (!owns(board, j, opponent)) continue
      // The opponent moves in its own direction, so it hits only from behind the blot
      const distance = (index - j) * opponent
      if (distance > 0 && distance in SHOTS) miss *= 1 - SHOTS[distance] / 36
    }
    return 1 - miss
  }
}
