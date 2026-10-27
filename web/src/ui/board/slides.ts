/** How the last step slides on the board: the moved checker from where it stood, a hit checker to the bar,
 * a borne off checker into the tray. A port of the flights in ui/board/board_widget.py. */
import { boardKey } from '../../ai/moveGen'
import { barOf, borneOff, type Board, type Player } from '../../game/rules'
import type { StepView } from '../gameModel'
import { BAR_SHOWN, MAX_SHOWN, barCenter, checkerCenter, slabRect, type Geometry, type Point2 } from './geometry'

export interface Slide {
  /** Where the checker starts, it slides to its place on the board */
  from: Point2
  /** Its size at the start, relative to its size at the end */
  scale: number
}

export interface Slides {
  /** The step the slides belong to, part of the element keys so every step starts its own slide */
  id: number
  /** point -> how the top checker there slides in */
  points: Map<number, Slide>
  /** player -> how the top checker on that bar slides in */
  bars: Map<number, Slide>
  /** The checker borne off by the last step, flying into the tray */
  offFlight: { from: Point2; to: Point2; player: Player } | null
}

/** The slides of the last step, while the board still shows the position it made */
export function slidesFor(g: Geometry, board: Board, step: StepView | null): Slides {
  const slides: Slides = { id: step?.id ?? 0, points: new Map(), bars: new Map(), offFlight: null }
  if (step === null || boardKey(step.after) !== boardKey(board)) return slides
  const { before, after, player, start, end, hit } = step
  const fromBar = start === barOf(player)
  const origin = fromBar
    ? barCenter(g, player, Math.min(before[start][0], BAR_SHOWN) - 1)
    : checkerCenter(g, start, Math.min(before[start][0], MAX_SHOWN) - 1)
  if (end === null) {
    const slab = slabRect(g, player, borneOff(after, player) - 1)
    slides.offFlight = { from: origin, to: [slab.x + slab.w / 2, slab.y + slab.h / 2], player }
    return slides
  }
  slides.points.set(end, { from: origin, scale: fromBar ? g.barChecker / g.checker : 1 })
  if (hit) {
    slides.bars.set(-player, { from: checkerCenter(g, end, 0), scale: g.checker / g.barChecker })
  }
  return slides
}

