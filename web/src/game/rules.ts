/**
 * Backgammon rules as pure functions over a board, shared by the game session and the computer player.
 * A port of rules.py: the same board layout, the same functions and the same move order.
 *
 * Board layout: index 0 is the bar of player 1 (white), index 25 is the bar of
 * player -1 (black), indices 1-24 are the points. Every cell is [count, owner].
 * Player 1 moves from low to high indices and bears off past 24,
 * player -1 moves from high to low indices and bears off below 1.
 */

export type Player = 1 | -1
export type Cell = [number, number]
export type Board = Cell[]
/** One die played: the checker's position and the die value */
export type Move = [number, number]

export interface Rng {
  /** A whole number from low to high, both included */
  randint(low: number, high: number): number
}

export const WHITE_BAR = 0
export const BLACK_BAR = 25
export const CHECKERS_PER_PLAYER = 15

export const mathRng: Rng = {
  randint: (low, high) => low + Math.floor(Math.random() * (high - low + 1)),
}

export function initBoard(): Board {
  return [
    [0, 1], [2, 1], [0, 0], [0, 0], [0, 0], [0, 0], [5, -1], [0, 0], [3, -1],
    [0, 0], [0, 0], [0, 0], [5, 1], [5, -1], [0, 0], [0, 0], [0, 0], [3, 1],
    [0, 0], [5, 1], [0, 0], [0, 0], [0, 0], [0, 0], [2, -1], [0, -1],
  ]
}

export function copyBoard(board: Board): Board {
  return board.map((cell) => [cell[0], cell[1]])
}

/** Rolls two dice, doubles give four moves */
export function rollDice(rng: Rng = mathRng): number[] {
  const die1 = rng.randint(1, 6)
  const die2 = rng.randint(1, 6)
  if (die1 === die2) return [die1, die1, die1, die1]
  return [die1, die2]
}

export function barOf(player: number): number {
  return player === 1 ? WHITE_BAR : BLACK_BAR
}

export function owns(board: Board, position: number, player: number): boolean {
  return board[position][0] > 0 && board[position][1] === player
}

export function hasEaten(board: Board, player: number): boolean {
  return board[barOf(player)][0] > 0
}

export function checkersLeft(board: Board, player: number): number {
  let total = 0
  for (const [count, owner] of board) if (owner === player) total += count
  return total
}

export function borneOff(board: Board, player: number): number {
  return CHECKERS_PER_PLAYER - checkersLeft(board, player)
}

export function canStartThrowing(board: Board, player: number): boolean {
  const [low, high] = player === 1 ? [19, 24] : [1, 6]
  for (let i = 0; i < board.length; i++) {
    if ((i < low || i > high) && owns(board, i, player)) return false
  }
  return true
}

export function checkMove(board: Board, player: number, position: number, jump: number): boolean {
  // The move must start inside the board, on a checker of the player
  if (position < 0 || position >= board.length || !owns(board, position, player)) return false

  // A checker on the bar must enter before any other checker moves
  if (hasEaten(board, player) && position !== barOf(player)) return false

  const destination = position + jump * player
  if (destination >= 1 && destination <= 24) {
    // The destination must be empty, hold only one opposing checker or belong to the player
    return board[destination][0] <= 1 || board[destination][1] === player
  }

  // Throwing a checker off the board
  if (!canStartThrowing(board, player)) return false
  const distance = player === 1 ? 25 - position : position
  if (jump === distance) return true
  // A higher die may be used only when no checker sits farther from home
  if (player === 1) {
    for (let i = 19; i < position; i++) if (owns(board, i, player)) return false
  } else {
    for (let i = position + 1; i < 7; i++) if (owns(board, i, player)) return false
  }
  return true
}

export interface Applied {
  /** (from, to) pairs: a hit checker going to the bar first, then the moved checker */
  movesMade: [number, number][]
  thrown: boolean
}

/** Applies a valid move on the board in place */
export function applyMove(board: Board, player: number, position: number, jump: number): Applied {
  const movesMade: [number, number][] = []
  board[position][0] -= 1
  if (board[position][0] === 0 && position !== barOf(player)) board[position][1] = 0

  const destination = position + jump * player
  if (destination < 1 || destination > 24) return { movesMade, thrown: true }

  if (board[destination][1] === -player && board[destination][0] === 1) {
    const eatenDest = barOf(-player)
    board[eatenDest][0] += 1
    board[eatenDest][1] = -player
    movesMade.push([destination, eatenDest])
    board[destination][0] = 0
  }
  board[destination][0] += 1
  board[destination][1] = player
  movesMade.push([position, destination])
  return { movesMade, thrown: false }
}

function distinctSorted(dice: number[]): number[] {
  return [...new Set(dice)].sort((a, b) => a - b)
}

function without(dice: number[], jump: number): number[] {
  const rest = [...dice]
  rest.splice(rest.indexOf(jump), 1)
  return rest
}

export function singleMoves(board: Board, player: number, dice: number[]): Move[] {
  const moves: Move[] = []
  const jumps = distinctSorted(dice)
  for (let i = 0; i < board.length; i++) {
    if (!owns(board, i, player)) continue
    for (const jump of jumps) {
      if (checkMove(board, player, i, jump)) moves.push([i, jump])
    }
  }
  return moves
}

/** The maximal number of dice the player can use from this board */
export function maxDiceUsed(board: Board, player: number, dice: number[]): number {
  if (dice.length === 0) return 0
  // Throwing off the last checker ends the game, the remaining dice are not needed
  if (checkersLeft(board, player) === 0) return dice.length
  let best = 0
  for (const [position, jump] of singleMoves(board, player, dice)) {
    const next = copyBoard(board)
    applyMove(next, player, position, jump)
    best = Math.max(best, 1 + maxDiceUsed(next, player, without(dice, jump)))
    if (best === dice.length) break
  }
  return best
}

/** Legal moves according to the rules: as many dice as possible must be used,
 * and when only one of two different dice can be used it must be the higher one */
export function possibleMoves(board: Board, player: number, dice: number[]): Move[] {
  let moves = singleMoves(board, player, dice)
  if (dice.length < 2 || moves.length === 0) return moves

  const used = moves.map(([position, jump]) => {
    const next = copyBoard(board)
    applyMove(next, player, position, jump)
    return 1 + maxDiceUsed(next, player, without(dice, jump))
  })

  const best = Math.max(...used)
  moves = moves.filter((_, i) => used[i] === best)
  if (best === 1 && new Set(dice).size === 2) {
    const highest = Math.max(...dice)
    const higher = moves.filter(([, jump]) => jump === highest)
    if (higher.length > 0) moves = higher
  }
  return moves
}

export function sameMove(a: Move, b: Move): boolean {
  return a[0] === b[0] && a[1] === b[1]
}
