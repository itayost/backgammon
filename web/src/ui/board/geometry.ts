/**
 * Board geometry in CSS pixels for the space the board gets, a port of ui/board/layout.py.
 *
 * At 904 x 692 it is the desktop board of the mockup. Narrower boards keep the same layout with
 * thinner frame parts, and in portrait the board may grow taller than the desktop proportions
 * so the points stay long enough to touch.
 */

export const DESKTOP_W = 904
export const DESKTOP_H = 692
/** Widest board: the desktop proportions */
export const MAX_ASPECT = DESKTOP_W / DESKTOP_H
/** Tallest board, for phones held upright */
export const MIN_ASPECT = 0.8
export const MAX_SHOWN = 5
export const BAR_SHOWN = 4

export interface Geometry {
  W: number
  H: number
  pad: number
  gap: number
  barW: number
  trayW: number
  fieldW: number
  leftX: number
  barX: number
  rightX: number
  trayX: number
  fieldPad: number
  pointGap: number
  pointW: number
  rowH: number
  topY: number
  bottomY: number
  midY: number
  midGap: number
  checker: number
  stackStep: number
  barChecker: number
  barStep: number
  barOffset: number
  die: number
  dieGap: number
  slabH: number
  slabStep: number
  /** Room at the outer end of each tray half for its OFF label */
  trayLabel: number
  frameRadius: number
  fieldRadius: number
  smallRadius: number
}

const clamp = (value: number, low: number, high: number) => Math.min(high, Math.max(low, value))

/** The board that fits in width x height */
export function geometry(width: number, height: number): Geometry {
  let W = Math.max(width, 240)
  let H = Math.max(height, 180)
  if (W / H > MAX_ASPECT) W = H * MAX_ASPECT
  else if (W / H < MIN_ASPECT) H = W / MIN_ASPECT
  const s = W / DESKTOP_W

  const pad = clamp(14 * s, 6, 14)
  const gap = clamp(10 * s, 4, 10)
  const barW = clamp(44 * s, 24, 44)
  const trayW = clamp(56 * s, 30, 56)
  const fieldW = (W - 2 * pad - barW - trayW - 3 * gap) / 2
  const leftX = pad
  const barX = leftX + fieldW + gap
  const rightX = barX + barW + gap
  const trayX = rightX + fieldW + gap
  const fieldPad = clamp(10 * s, 4, 10)
  const pointGap = clamp(4 * s, 1.5, 4)
  const pointW = (fieldW - 2 * fieldPad - 5 * pointGap) / 6
  // Small checkers fill their point, large ones leave the point's edges showing
  const checker = pointW * (pointW < 36 ? 0.97 : 0.9)

  const die = clamp(48 * s, 26, 48)
  const midGap = die * 1.75
  const rowH = (H - 2 * pad - 2 * fieldPad - midGap) / 2
  const topY = pad + fieldPad
  const bottomY = H - pad - fieldPad - rowH
  // Five checkers stand in a point; when the point is short they overlap a little
  const stackStep = Math.min(checker + Math.max(1, s), (rowH - checker) / (MAX_SHOWN - 1))

  const barChecker = Math.min(checker * 0.84, barW - 2)
  const half = (H - 2 * pad) / 2
  const trayLabel = trayW < 44 ? 30 : 34
  const slabStep = Math.min(12, (half - trayLabel - 8) / 15)

  return {
    W, H, pad, gap, barW, trayW, fieldW, leftX, barX, rightX, trayX, fieldPad, pointGap, pointW, rowH,
    topY, bottomY, midY: H / 2, midGap, checker, stackStep,
    barChecker, barStep: barChecker + 2, barOffset: midGap * 0.405,
    die, dieGap: clamp(12 * s, 6, 12),
    slabH: slabStep - Math.max(1.5, 2 * s), slabStep, trayLabel,
    frameRadius: clamp(16 * s, 8, 16), fieldRadius: clamp(8 * s, 4, 8), smallRadius: clamp(6 * s, 3, 6),
  }
}

export interface PointRect {
  x: number
  y: number
  w: number
  h: number
  top: boolean
}

/** The triangle area of a point. Top row left to right: 12..7 | 6..1,
 * bottom row: 13..18 | 19..24 (white's home bottom right). */
export function pointRect(g: Geometry, point: number): PointRect {
  let fieldX: number, column: number, top: boolean
  if (point >= 1 && point <= 6) [fieldX, column, top] = [g.rightX, 6 - point, true]
  else if (point >= 7 && point <= 12) [fieldX, column, top] = [g.leftX, 12 - point, true]
  else if (point >= 13 && point <= 18) [fieldX, column, top] = [g.leftX, point - 13, false]
  else if (point >= 19 && point <= 24) [fieldX, column, top] = [g.rightX, point - 19, false]
  else throw new Error(`no point ${point}`)
  const x = fieldX + g.fieldPad + column * (g.pointW + g.pointGap)
  return { x, y: top ? g.topY : g.bottomY, w: g.pointW, h: g.rowH, top }
}

export type Point2 = [number, number]

/** Center of the checker in a stack slot, slot 0 sits at the board edge */
export function checkerCenter(g: Geometry, point: number, slot: number): Point2 {
  const { x, y, w, h, top } = pointRect(g, point)
  const offset = g.checker / 2 + slot * g.stackStep
  return [x + w / 2, top ? y + offset : y + h - offset]
}

/** White waits on the top half of the bar, black on the bottom half */
export function barCenter(g: Geometry, player: number, slot: number): Point2 {
  const offset = g.barOffset + slot * g.barStep
  return [g.barX + g.barW / 2, player === 1 ? g.midY - offset : g.midY + offset]
}

export interface Rect {
  x: number
  y: number
  w: number
  h: number
}

/** White bears off into the bottom half of the tray, next to its home, black into the top half */
export function trayRect(g: Geometry, player: number): Rect {
  const half = (g.H - 2 * g.pad) / 2
  return player === 1
    ? { x: g.trayX, y: g.pad + half, w: g.trayW, h: half }
    : { x: g.trayX, y: g.pad, w: g.trayW, h: half }
}

export function slabRect(g: Geometry, player: number, index: number): Rect {
  const inset = Math.min(8, g.trayW * 0.15)
  const w = g.trayW - 2 * inset
  return player === 1
    ? { x: g.trayX + inset, y: g.H - g.pad - g.trayLabel - (index + 1) * g.slabStep, w, h: g.slabH }
    : { x: g.trayX + inset, y: g.pad + g.trayLabel + index * g.slabStep, w, h: g.slabH }
}

export function diceCenters(g: Geometry, count: number): Point2[] {
  const total = count * g.die + (count - 1) * g.dieGap
  const start = g.rightX + g.fieldW / 2 - total / 2 + g.die / 2
  return Array.from({ length: count }, (_, i) => [start + i * (g.die + g.dieGap), g.midY])
}

export type Target = ['point', number] | ['bar', null] | ['tray', null]

export function sameTarget(a: Target | null, b: Target | null): boolean {
  return a !== null && b !== null && a[0] === b[0] && a[1] === b[1]
}

/** The point whose column holds x in the field starting at fieldX, or null between fields */
function column(g: Geometry, fieldX: number, x: number): number | null {
  const inner = x - fieldX - g.fieldPad + g.pointGap / 2
  if (x < fieldX || x > fieldX + g.fieldW) return null
  return clamp(Math.floor(inner / (g.pointW + g.pointGap)), 0, 5)
}

/** What a press at (x, y) hits. A point owns its whole half column, from the frame to the middle
 * of the board, so a touch does not have to land on the narrow triangle. */
export function hitTest(g: Geometry, x: number, y: number): Target | null {
  if (y < g.pad || y > g.H - g.pad) return null
  const top = y < g.midY
  const left = column(g, g.leftX, x)
  if (left !== null) return ['point', top ? 12 - left : 13 + left]
  const right = column(g, g.rightX, x)
  if (right !== null) return ['point', top ? 6 - right : 19 + right]
  if (x >= g.barX - g.gap / 2 && x <= g.barX + g.barW + g.gap / 2) return ['bar', null]
  if (x >= g.trayX - g.gap / 2 && x <= g.trayX + g.trayW) return ['tray', null]
  return null
}

/** The x of a point's column center */
export function pointCenterX(g: Geometry, point: number): number {
  const { x, w } = pointRect(g, point)
  return x + w / 2
}
