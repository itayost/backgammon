import type { Level } from '../game/config'
import type { Board, Move } from '../game/rules'
import type { ThinkRequest, ThinkResult } from './worker'

/** Chooses the computer's move; null when it failed. cancel() drops the questions still open,
 * dispose() frees what the thinker holds once its game is over. */
export interface Thinker {
  think(level: Level, board: Board, player: number, dice: number[]): Promise<Move[] | null>
  cancel(): void
  dispose?(): void
}

/** Thinks in a Web Worker. Cancelling ends the worker, so a long search for a game that is gone
 * does not hold up the next one; a new worker starts with the next question. */
export class WorkerThinker implements Thinker {
  private worker: Worker | null = null
  private nextId = 1
  private open = new Map<number, (steps: Move[] | null) => void>()

  think(level: Level, board: Board, player: number, dice: number[]): Promise<Move[] | null> {
    const worker = this.ensureWorker()
    const id = this.nextId++
    return new Promise((resolve) => {
      this.open.set(id, resolve)
      worker.postMessage({ id, level, board, player, dice } satisfies ThinkRequest)
    })
  }

  cancel() {
    if (this.open.size === 0) return
    this.dispose()
  }

  dispose() {
    this.worker?.terminate()
    this.worker = null
    this.settleAll(null)
  }

  private ensureWorker(): Worker {
    if (this.worker === null) {
      const worker = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' })
      worker.onmessage = (event: MessageEvent<ThinkResult>) => {
        const resolve = this.open.get(event.data.id)
        this.open.delete(event.data.id)
        resolve?.(event.data.steps)
      }
      worker.onerror = (event) => {
        console.error('the computer player stopped', event.message)
        worker.terminate()
        this.worker = null
        this.settleAll(null)
      }
      this.worker = worker
    }
    return this.worker
  }

  private settleAll(steps: Move[] | null) {
    const waiting = [...this.open.values()]
    this.open.clear()
    for (const resolve of waiting) resolve(steps)
  }
}
