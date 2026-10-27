/**
 * The board, drawn in SVG at the size it gets: a port of ui/board/board_widget.py for mouse,
 * touch and keyboard. A checker is moved by pressing it and then where it goes, or by dragging it.
 */
import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent } from 'react'
import { boardKey } from '../../ai/moveGen'
import { barOf, borneOff, type Player } from '../../game/rules'
import type { BoardView, StepView } from '../gameModel'
import {
  BAR_SHOWN, MAX_SHOWN, barCenter, checkerCenter, diceCenters, geometry, hitTest, pointCenterX, pointRect,
  slabRect, trayRect, type Geometry, type Point2, type Target,
} from './geometry'
import { slidesFor, type Slide, type Slides } from './slides'

const PIPS: Record<number, number[]> = {
  1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8],
}
// A press that moves less than this is a tap, not a drag
const DRAG_THRESHOLD = 6
// A checker dragged by a finger is drawn this many checker sizes above it, so the finger does not hide it
const TOUCH_LIFT = 0.8

interface BoardProps {
  view: BoardView
  step: StepView | null
  onPress(target: Target): void
  onPick(point: number): void
  onDrop(target: Target): void
  onNavigate(step: number): void
  onActivate(): void
  onCancel(): void
}

interface Drag {
  pointerId: number
  point: number
  start: Point2
  at: Point2
  moved: boolean
  /** The checker was already picked, so a tap on it drops it */
  wasSelected: boolean
  touch: boolean
}

type Ring = 'selected' | 'movable' | null

function useSize<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [size, setSize] = useState<[number, number] | null>(null)
  useLayoutEffect(() => {
    const element = ref.current
    if (element === null) return
    const measure = () => setSize([element.clientWidth, element.clientHeight])
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [])
  return [ref, size] as const
}

export function Board(props: BoardProps) {
  const [areaRef, size] = useSize<HTMLDivElement>()
  return (
    <div className="board-area" ref={areaRef}>
      {size !== null && size[0] > 0 && size[1] > 0 && <BoardSvg {...props} g={geometry(size[0], size[1])} />}
    </div>
  )
}

function BoardSvg({ view, step, onPress, onPick, onDrop, onNavigate, onActivate, onCancel, g }: BoardProps & { g: Geometry }) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [drag, setDrag] = useState<Drag | null>(null)
  const [focusVisible, setFocusVisible] = useState(false)
  const bar = barOf(view.player)

  // A new position or turn ends any drag in progress
  const dragKey = `${boardKey(view.board)}|${view.player}|${[...view.pickable].join(',')}`
  useEffect(() => setDrag(null), [dragKey])

  const toBoard = (event: PointerEvent): Point2 => {
    const rect = svgRef.current!.getBoundingClientRect()
    return [event.clientX - rect.left, event.clientY - rect.top]
  }

  /** On a touch screen a press next to a checker or point that can be used counts as on it */
  const snap = (target: Target | null, [x, y]: Point2, points: Set<number>, tray: boolean, touch: boolean): Target | null => {
    const fits = (t: Target | null) => t !== null && (
      (t[0] === 'point' && points.has(t[1])) || (t[0] === 'bar' && points.has(bar)) || (t[0] === 'tray' && tray))
    if (!touch || fits(target)) return target
    const top = y < g.midY
    let best: Target | null = null
    let distance = g.pointW + g.pointGap
    for (const point of points) {
      if (point === bar) {
        const d = Math.abs(g.barX + g.barW / 2 - x)
        if (d < distance) [best, distance] = [['bar', null], d]
      } else if (pointRect(g, point).top === top) {
        const d = Math.abs(pointCenterX(g, point) - x)
        if (d < distance) [best, distance] = [['point', point], d]
      }
    }
    if (tray && Math.abs(g.trayX + g.trayW / 2 - x) < distance) best = ['tray', null]
    return best ?? target
  }

  const pointOf = (target: Target): number | null =>
    target[0] === 'point' ? target[1] : target[0] === 'bar' ? bar : null

  const handlePointerDown = (event: PointerEvent<SVGSVGElement>) => {
    if (event.button !== 0 || drag !== null) return
    const at = toBoard(event)
    const touch = event.pointerType !== 'mouse'
    const hit = hitTest(g, ...at)
    const asPick = snap(hit, at, view.pickable, false, touch)
    const picked = asPick !== null ? pointOf(asPick) : null
    // Pressing a target of the picked checker moves it, even when that point also holds a movable checker
    const asTarget = view.selected !== null ? snap(hit, at, view.targets, view.trayTarget, touch) : null
    const isTarget = asTarget !== null && (asTarget[0] === 'tray' ? view.trayTarget : view.targets.has(pointOf(asTarget)!))
    if (isTarget) {
      onPress(asTarget)
      return
    }
    if (picked !== null && view.pickable.has(picked)) {
      event.currentTarget.setPointerCapture(event.pointerId)
      setDrag({ pointerId: event.pointerId, point: picked, start: at, at, moved: false,
                wasSelected: view.selected === picked, touch })
      onPick(picked)
      return
    }
    if (hit !== null) onPress(hit)
  }

  const handlePointerMove = (event: PointerEvent<SVGSVGElement>) => {
    const at = toBoard(event)
    if (drag === null || drag.pointerId !== event.pointerId) {
      if (event.pointerType === 'mouse') {
        const hit = hitTest(g, ...at)
        const point = hit !== null ? pointOf(hit) : null
        const clickable = hit !== null && ((point !== null && (view.pickable.has(point) || view.targets.has(point)))
          || (hit[0] === 'tray' && view.trayTarget))
        event.currentTarget.style.cursor = clickable ? 'pointer' : ''
      }
      return
    }
    const moved = drag.moved || Math.hypot(at[0] - drag.start[0], at[1] - drag.start[1]) > DRAG_THRESHOLD
    setDrag({ ...drag, at, moved })
  }

  const handlePointerUp = (event: PointerEvent<SVGSVGElement>) => {
    if (drag === null || drag.pointerId !== event.pointerId) return
    setDrag(null)
    if (drag.moved) {
      const [x, y] = toBoard(event)
      // It lands where it is drawn
      const at: Point2 = [x, y - (drag.touch ? g.checker * TOUCH_LIFT : 0)]
      const target = snap(hitTest(g, ...at), at, view.targets, view.trayTarget, drag.touch)
      if (target !== null) onDrop(target)
    } else if (drag.wasSelected) {
      onPress(drag.point === bar ? ['bar', null] : ['point', drag.point])
    }
  }

  const handleKeyDown = (event: KeyboardEvent<SVGSVGElement>) => {
    const keys: Record<string, () => void> = {
      ArrowLeft: () => onNavigate(-1), ArrowUp: () => onNavigate(-1),
      ArrowRight: () => onNavigate(1), ArrowDown: () => onNavigate(1),
      Enter: onActivate, ' ': onActivate, Escape: onCancel,
    }
    const action = keys[event.key]
    if (action === undefined) return
    event.preventDefault()
    event.stopPropagation()
    action()
  }

  const lifted = drag?.moved ? drag.point : null
  const slides = slidesFor(g, view.board, step)

  return (
    <svg
      ref={svgRef}
      className="board"
      width={g.W}
      height={g.H}
      viewBox={`0 0 ${g.W} ${g.H}`}
      style={{ borderRadius: g.frameRadius }}
      tabIndex={0}
      role="application"
      aria-label="Backgammon board"
      aria-describedby="board-help"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={() => setDrag(null)}
      onKeyDown={handleKeyDown}
      onFocus={(event) => setFocusVisible(event.currentTarget.matches(':focus-visible'))}
      onBlur={() => setFocusVisible(false)}
    >
      <Frame g={g} barMovable={view.sources.has(bar)} />
      {Array.from({ length: 24 }, (_, i) => i + 1).map((point) => (
        <PointShape key={point} g={g} point={point} target={view.targets.has(point)} movable={view.sources.has(point)} />
      ))}
      {Array.from({ length: 24 }, (_, i) => i + 1).map((point) => (
        <Stack key={point} g={g} view={view} point={point} lifted={lifted === point} slides={slides} />
      ))}
      <BarStacks g={g} view={view} lifted={lifted === bar} slides={slides} />
      <Tray g={g} view={view} slides={slides} />
      <Dice g={g} dice={view.dice} />
      {slides.offFlight !== null && (
        <Checker key={`off-${slides.id}`} center={slides.offFlight.to} size={g.checker}
                 owner={slides.offFlight.player} className="fly-off" slide={{ from: slides.offFlight.from, scale: 1 }} />
      )}
      {drag?.moved && (
        <Checker owner={view.player} size={g.checker} className="dragged"
                 center={[drag.at[0], drag.at[1] - (drag.touch ? g.checker * TOUCH_LIFT : 0)]} ring="selected" />
      )}
      {focusVisible && view.cursor !== null && <Cursor g={g} cursor={view.cursor} player={view.player} />}
    </svg>
  )
}

function Frame({ g, barMovable }: { g: Geometry; barMovable: boolean }) {
  const inner = g.H - 2 * g.pad
  return (
    <g>
      <rect width={g.W} height={g.H} rx={g.frameRadius} fill="var(--color-board-frame)" />
      {[g.leftX, g.rightX].map((x) => (
        <rect key={x} x={x} y={g.pad} width={g.fieldW} height={inner} rx={g.fieldRadius} fill="var(--color-board-felt)" />
      ))}
      <rect x={g.barX} y={g.pad} width={g.barW} height={inner} rx={g.smallRadius} fill="var(--color-board-bar)"
            data-bar data-movable={barMovable || undefined} />
      <rect x={g.trayX} y={g.pad} width={g.trayW} height={inner} rx={g.smallRadius} fill="var(--color-board-bar)" />
    </g>
  )
}

function PointShape({ g, point, target, movable }: { g: Geometry; point: number; target: boolean; movable: boolean }) {
  const { x, y, w, h, top } = pointRect(g, point)
  const points = top ? `${x},${y} ${x + w},${y} ${x + w / 2},${y + h}` : `${x},${y + h} ${x + w},${y + h} ${x + w / 2},${y}`
  const fill = target ? 'var(--color-accent)' : point % 2 === 0 ? 'var(--color-point-dark)' : 'var(--color-point-light)'
  return <polygon points={points} fill={fill} data-point={point} data-target={target || undefined} data-movable={movable || undefined} />
}

interface CheckerProps {
  center: Point2
  size: number
  owner: number
  ring?: Ring
  label?: string | null
  slide?: Slide
  className?: string
}

function Checker({ center: [cx, cy], size, owner, ring = null, label = null, slide, className }: CheckerProps) {
  const kind = owner === 1 ? 'white' : 'black'
  const radius = size / 2
  const rim = size * 0.06
  const style = slide
    ? ({ '--dx': slide.from[0] - cx, '--dy': slide.from[1] - cy, '--s': slide.scale } as CSSProperties)
    : undefined
  return (
    <g className={[slide ? 'slide' : '', className ?? ''].join(' ').trim() || undefined} style={style}>
      <circle cx={cx} cy={cy + Math.max(1.5, size * 0.04)} r={radius} fill="rgba(0, 0, 0, 0.35)" />
      <circle cx={cx} cy={cy} r={radius - rim / 2} fill={`var(--color-checker-${kind})`}
              stroke={`var(--color-checker-${kind}-rim)`} strokeWidth={rim} />
      {ring === 'selected' && (
        <circle cx={cx} cy={cy} r={radius + 2.5} fill="none" stroke="var(--color-accent)" strokeWidth={3} />
      )}
      {ring === 'movable' && (
        <circle cx={cx} cy={cy} r={radius + 2} fill="none" stroke="var(--color-accent)" strokeOpacity={0.75} strokeWidth={2} />
      )}
      {label !== null && (
        <text x={cx} y={cy} className="checker-count" fontSize={Math.max(9, size * 0.36)}
              fill={owner === 1 ? 'var(--color-accent-ink)' : 'var(--color-text)'}>
          {label}
        </text>
      )}
    </g>
  )
}

function Stack({ g, view, point, lifted, slides }: { g: Geometry; view: BoardView; point: number; lifted: boolean; slides: Slides }) {
  const [total, owner] = view.board[point]
  const count = total - (lifted ? 1 : 0)
  const shown = Math.min(count, MAX_SHOWN)
  const checkers = []
  for (let slot = 0; slot < shown; slot++) {
    const isTop = slot === shown - 1
    let ring: Ring = null
    if (isTop && point === view.selected && !lifted) ring = 'selected'
    else if (isTop && view.sources.has(point) && view.selected === null) ring = 'movable'
    const slide = isTop && !lifted ? slides.points.get(point) : undefined
    checkers.push(
      <Checker key={slide ? `${slot}-slide-${slides.id}` : slot} center={checkerCenter(g, point, slot)}
               size={g.checker} owner={owner} ring={ring}
               label={isTop && count > MAX_SHOWN ? String(count) : null} slide={slide} />,
    )
  }
  return (
    <g>
      {checkers}
      {view.targets.has(point) && shown < MAX_SHOWN && <Landing g={g} center={checkerCenter(g, point, shown)} />}
    </g>
  )
}

function Landing({ g, center: [cx, cy] }: { g: Geometry; center: Point2 }) {
  return (
    <circle cx={cx} cy={cy} r={g.checker / 2 - 1} fill="var(--color-accent-ink)" fillOpacity={0.12}
            stroke="var(--color-accent-ink)" strokeWidth={2} strokeDasharray="4 3" />
  )
}

function BarStacks({ g, view, lifted, slides }: { g: Geometry; view: BoardView; lifted: boolean; slides: Slides }) {
  return (
    <g>
      {([1, -1] as Player[]).map((player) => {
        const bar = barOf(player)
        const count = view.board[bar][0] - (lifted && player === view.player ? 1 : 0)
        const shown = Math.min(count, BAR_SHOWN)
        return Array.from({ length: shown }, (_, slot) => {
          const isTop = slot === shown - 1
          let ring: Ring = null
          if (isTop && view.selected === bar && !lifted) ring = 'selected'
          else if (isTop && view.sources.has(bar) && view.selected === null) ring = 'movable'
          const slide = isTop ? slides.bars.get(player) : undefined
          return (
            <Checker key={`${player}-${slot}${slide ? `-slide-${slides.id}` : ''}`} center={barCenter(g, player, slot)}
                     size={g.barChecker} owner={player} ring={ring}
                     label={isTop && count > BAR_SHOWN ? String(count) : null} slide={slide} />
          )
        })
      })}
    </g>
  )
}

function Tray({ g, view, slides }: { g: Geometry; view: BoardView; slides: Slides }) {
  const narrow = g.trayW < 44
  return (
    <g>
      {view.trayTarget && (() => {
        const { x, y, w, h } = trayRect(g, view.player)
        return <rect x={x + 1} y={y + 1} width={w - 2} height={h - 2} rx={g.smallRadius} fill="var(--color-accent)"
                     fillOpacity={0.12} stroke="var(--color-accent)" strokeWidth={2} data-tray data-target />
      })()}
      {([1, -1] as Player[]).map((player) => {
        const off = borneOff(view.board, player)
        const kind = player === 1 ? 'white' : 'black'
        const { x, y, w, h } = trayRect(g, player)
        const labelY = player === 1 ? y + h - g.trayLabel / 2 : y + g.trayLabel / 2
        return (
          <g key={player}>
            {Array.from({ length: off }, (_, index) => {
              const slab = slabRect(g, player, index)
              // The slab of a checker still flying in shows when it lands
              const landing = slides.offFlight !== null && index === off - 1 && player === view.player
              return (
                <rect key={`${index}${landing ? `-landing-${slides.id}` : ''}`} className={landing ? 'slab-land' : undefined}
                      x={slab.x} y={slab.y} width={slab.w} height={slab.h} rx={Math.min(3, slab.h / 3)}
                      fill={`var(--color-checker-${kind})`} stroke={`var(--color-checker-${kind}-rim)`} strokeWidth={1} />
              )
            })}
            <text className="tray-label" x={x + w / 2} y={labelY} fontSize={narrow ? 9.5 : 11}>
              {narrow
                ? <><tspan x={x + w / 2} dy="-0.55em">OFF</tspan><tspan x={x + w / 2} dy="1.2em">{off}</tspan></>
                : `OFF ${off}`}
            </text>
          </g>
        )
      })}
    </g>
  )
}

function Dice({ g, dice }: { g: Geometry; dice: BoardView['dice'] }) {
  const centers = diceCenters(g, dice.length)
  const radius = g.die * (10 / 48)
  const cell = (g.die - g.die * (14 / 48)) / 3
  const inset = g.die * (7 / 48)
  return (
    <g>
      {dice.map(([value, used], i) => {
        const [cx, cy] = centers[i]
        const x = cx - g.die / 2
        const y = cy - g.die / 2
        return (
          <g key={i} opacity={used ? 0.35 : 1} className="die">
            <rect x={x} y={y + g.die / 12} width={g.die} height={g.die} rx={radius} fill="rgba(0, 0, 0, 0.4)" />
            <rect x={x} y={y} width={g.die} height={g.die} rx={radius} fill="var(--color-checker-white)" />
            {PIPS[value].map((index) => (
              <circle key={index} cx={x + inset + ((index % 3) + 0.5) * cell} cy={y + inset + (Math.floor(index / 3) + 0.5) * cell}
                      r={g.die / 12} fill="var(--color-accent-ink)" />
            ))}
          </g>
        )
      })}
    </g>
  )
}

function Cursor({ g, cursor, player }: { g: Geometry; cursor: Target; player: Player }) {
  let rect: { x: number; y: number; w: number; h: number }
  if (cursor[0] === 'point') {
    const { x, y, w, h } = pointRect(g, cursor[1])
    rect = { x: x - 3, y: y - 3, w: w + 6, h: h + 6 }
  } else if (cursor[0] === 'bar') {
    rect = { x: g.barX - 3, y: g.pad + 2, w: g.barW + 6, h: g.H - 2 * g.pad - 4 }
  } else {
    const { x, y, w, h } = trayRect(g, player)
    rect = { x: x - 3, y: y - 3, w: w + 6, h: h + 6 }
  }
  return (
    <rect x={rect.x} y={rect.y} width={rect.w} height={rect.h} rx={6} fill="none"
          stroke="var(--color-text)" strokeWidth={2} strokeDasharray="6 4" />
  )
}
