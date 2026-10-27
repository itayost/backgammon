import { applyMove, copyBoard, possibleMoves, type Board, type Move, type Rng } from '../src/game/rules'

export function emptyBoard(): Board {
  const board: Board = Array.from({ length: 26 }, () => [0, 0])
  board[0] = [0, 1]
  board[25] = [0, -1]
  return board
}

/** Returns the given dice values in order */
export function sequenceRng(values: number[]): Rng {
  const queue = [...values]
  return { randint: () => queue.shift()! }
}

/** A seeded generator (mulberry32), so random tests repeat */
export function seeded(seed: number): () => number {
  let state = seed >>> 0
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let t = state
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function seededRng(seed: number): Rng {
  const random = seeded(seed)
  return { randint: (low, high) => low + Math.floor(random() * (high - low + 1)) }
}

export function pick<T>(random: () => number, items: T[]): T {
  return items[Math.floor(random() * items.length)]
}

/** Plays the steps checking each one is legal, returns the board and the dice left */
export function play(board: Board, player: number, dice: number[], steps: Move[]): [Board, number[]] {
  const result = copyBoard(board)
  const left = [...dice]
  for (const [position, jump] of steps) {
    const legal = possibleMoves(result, player, left)
    if (!legal.some(([p, j]) => p === position && j === jump)) throw new Error(`illegal step ${position}/${jump}`)
    applyMove(result, player, position, jump)
    left.splice(left.indexOf(jump), 1)
  }
  return [result, left]
}
