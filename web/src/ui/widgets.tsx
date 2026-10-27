/** Small building blocks styled by src/styles/app.css, ports of ui/widgets */
import { useEffect, useRef, type ButtonHTMLAttributes, type KeyboardEvent, type ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  /** 'large' for the main action of a screen or dialog */
  size?: 'normal' | 'large'
}

export function Button({ variant = 'secondary', size = 'normal', className, ...rest }: ButtonProps) {
  return <button type="button" className={['button', variant, size === 'large' ? 'large' : '', className ?? ''].join(' ').trim()} {...rest} />
}

/** Stroke icons drawn on a 24 unit grid, like the icons of the mockups */
const ICONS = {
  back: ['M15 18 9 12 15 6'],
  menu: ['M4 7h16', 'M4 12h16', 'M4 17h16'],
}

export function IconButton({ icon, label, onClick }: { icon: keyof typeof ICONS; label: string; onClick(): void }) {
  return (
    <button type="button" className="icon-button" aria-label={label} title={label} onClick={onClick}>
      <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
        {ICONS[icon].map((d) => (
          <path key={d} d={d} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        ))}
      </svg>
    </button>
  )
}

/** A checker swatch: 1 white, -1 black, null for random (half and half) */
export function CheckerDot({ player, size = 28 }: { player: number | null; size?: number }) {
  const rim = size * 0.1
  const r = size / 2 - rim / 2
  const c = size / 2
  return (
    <svg className="checker-dot" width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
      {player === null ? (
        <>
          <path d={`M${c} 0 A${c} ${c} 0 0 0 ${c} ${size} Z`} fill="var(--color-checker-white)" />
          <path d={`M${c} 0 A${c} ${c} 0 0 1 ${c} ${size} Z`} fill="var(--color-checker-black)" />
          <circle cx={c} cy={c} r={r} fill="none" stroke="var(--color-text-muted)" strokeWidth={rim} />
        </>
      ) : (
        <circle cx={c} cy={c} r={r} fill={`var(--color-checker-${player === 1 ? 'white' : 'black'})`}
                stroke={`var(--color-checker-${player === 1 ? 'white' : 'black'}-rim)`} strokeWidth={rim} />
      )}
    </svg>
  )
}

/** Arrow keys move the choice inside a radio group, like native radio buttons */
function arrowKeys<T>(values: T[], value: T, onChange: (value: T) => void) {
  return (event: KeyboardEvent<HTMLElement>) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key]
    if (step === undefined) return
    event.preventDefault()
    const next = values[(values.indexOf(value) + step + values.length) % values.length]
    onChange(next)
    const group = event.currentTarget
    requestAnimationFrame(() => group.querySelector<HTMLElement>('[aria-checked="true"]')?.focus())
  }
}

interface SegmentedProps<T extends string> {
  options: [string, T][]
  value: T
  onChange(value: T): void
  label: string
}

export function SegmentedControl<T extends string>({ options, value, onChange, label }: SegmentedProps<T>) {
  return (
    <div className="segments" role="radiogroup" aria-label={label}
         onKeyDown={arrowKeys(options.map(([, v]) => v), value, onChange)}>
      {options.map(([text, option]) => (
        <button key={option} type="button" role="radio" aria-checked={option === value}
                tabIndex={option === value ? 0 : -1} className="segment" onClick={() => onChange(option)}>
          {text}
        </button>
      ))}
    </div>
  )
}

export interface Choice<T> {
  label: string
  value: T
  text?: string
  /** Shows a checker swatch: 1, -1, or null for random */
  player?: number | null
}

interface ChoiceGroupProps<T extends string> {
  options: Choice<T>[]
  value: T
  onChange(value: T): void
  label: string
  className?: string
}

/** A row of large selectable cards, each a title with an optional description or a checker swatch */
export function ChoiceGroup<T extends string>({ options, value, onChange, label, className }: ChoiceGroupProps<T>) {
  return (
    <div className={['choices', className ?? ''].join(' ').trim()} role="radiogroup" aria-label={label}
         onKeyDown={arrowKeys(options.map((o) => o.value), value, onChange)}>
      {options.map((option) => (
        <button key={option.value} type="button" role="radio" aria-checked={option.value === value}
                tabIndex={option.value === value ? 0 : -1}
                className={['choice', option.text ? 'tall' : ''].join(' ').trim()} onClick={() => onChange(option.value)}>
          {option.player !== undefined && <CheckerDot player={option.player} />}
          <span className="choice-texts">
            <span className="choice-title">{option.label}</span>
            {option.text && <span className="muted">{option.text}</span>}
          </span>
        </button>
      ))}
    </div>
  )
}

interface DialogProps {
  labelledBy: string
  wide?: boolean
  children: ReactNode
}

/**
 * Covers the screen with the night scrim and centers a dialog card on it, so the board stays visible
 * behind, dimmed and out of play. Focus starts on the dialog's first button and stays inside it.
 */
export function Dialog({ labelledBy, wide = false, children }: DialogProps) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    ref.current?.querySelector<HTMLElement>('button')?.focus()
    return () => previous?.focus?.()
  }, [])

  const trapFocus = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Tab') return
    const buttons = [...ref.current!.querySelectorAll<HTMLElement>('button:not([disabled])')]
    if (!buttons.length) return
    const first = buttons[0]
    const last = buttons[buttons.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  return (
    <div className="scrim" onPointerDown={(event) => event.stopPropagation()}>
      <div ref={ref} className={['dialog', wide ? 'wide' : ''].join(' ').trim()} role="dialog" aria-modal="true"
           aria-labelledby={labelledBy} onKeyDown={trapFocus}>
        {children}
      </div>
    </div>
  )
}
