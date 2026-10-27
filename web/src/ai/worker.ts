/// <reference lib="webworker" />
/** Thinks for the computer away from the page, so the board keeps animating while it searches */
import type { Level } from '../game/config'
import type { Board, Move } from '../game/rules'
import { ComputerPlayer } from './player'

export interface ThinkRequest {
  id: number
  level: Level
  board: Board
  player: number
  dice: number[]
}

export interface ThinkResult {
  id: number
  /** null when the computer failed to choose a move */
  steps: Move[] | null
}

const players = new Map<Level, ComputerPlayer>()

self.onmessage = (event: MessageEvent<ThinkRequest>) => {
  const { id, level, board, player, dice } = event.data
  let steps: Move[] | null
  try {
    if (!players.has(level)) players.set(level, new ComputerPlayer(level))
    steps = players.get(level)!.choose(board, player, dice)
  } catch (error) {
    console.error('the computer failed to choose a move', error)
    steps = null
  }
  self.postMessage({ id, steps } satisfies ThinkResult)
}
