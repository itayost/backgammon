import { applyMove, copyBoard, possibleMoves, type Board, type Move } from '../game/rules'

/** A key that tells positions apart. An empty cell may keep its last owner, so it is ignored. */
export function boardKey(board: Board): string {
  return board.map(([count, owner]) => `${count}:${count ? owner : 0}`).join(',')
}

export interface FullMove {
  board: Board
  /** The (position, jump) steps in the order the session accepts them */
  steps: Move[]
}

/** All the distinct positions the player can reach with the dice.
 * When there is no legal move the result holds the board as it is with no steps. */
export function fullMoves(board: Board, player: number, dice: number[]): FullMove[] {
  const results = new Map<string, FullMove>()

  const expand = (current: Board, remaining: number[], steps: Move[]) => {
    const moves = possibleMoves(current, player, remaining)
    if (moves.length === 0) {
      const key = boardKey(current)
      if (!results.has(key)) results.set(key, { board: current, steps })
      return
    }
    for (const [position, jump] of moves) {
      const next = copyBoard(current)
      applyMove(next, player, position, jump)
      const rest = [...remaining]
      rest.splice(rest.indexOf(jump), 1)
      expand(next, rest, [...steps, [position, jump]])
    }
  }

  expand(copyBoard(board), [...dice], [])
  return [...results.values()]
}

/** The 21 distinct rolls with their probability */
export function allRolls(): [number[], number][] {
  const rolls: [number[], number][] = []
  for (let die1 = 1; die1 <= 6; die1++) {
    for (let die2 = die1; die2 <= 6; die2++) {
      if (die1 === die2) rolls.push([[die1, die1, die1, die1], 1 / 36])
      else rolls.push([[die1, die2], 2 / 36])
    }
  }
  return rolls
}
