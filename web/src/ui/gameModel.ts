/**
 * Everything the Game screen shows and does, without React: a port of ui/screens/game.py.
 * The screen renders view() and calls the actions; subscribe() tells it when to render again.
 */
import { AIController } from '../ai/controller'
import { WorkerThinker, type Thinker } from '../ai/thinker'
import { COLOR_NAMES, capitalize, type ComputerLevels, type GameConfig } from '../game/config'
import { barOf, copyBoard, type Board, type Player } from '../game/rules'
import { GameSession, NO_LEGAL_MOVES, type SessionEvent } from '../game/session'
import { sameTarget, type Target } from './board/geometry'

/** One die on the board and whether it is played */
export type DieView = [number, boolean]

export interface BoardView {
  board: Board
  dice: DieView[]
  /** Points (0 and 25 for the bars) with a checker that can move, marked when hints are on */
  sources: Set<number>
  /** The same points whether hints are on or not: where a drag may start */
  pickable: Set<number>
  selected: number | null
  /** Points the selected checker can reach */
  targets: Set<number>
  /** The selected checker can bear off */
  trayTarget: boolean
  player: Player
  cursor: Target | null
}

/** The last checker that moved, for the board to slide it */
export interface StepView {
  id: number
  before: Board
  after: Board
  player: Player
  start: number
  end: number | null
  hit: boolean
}

export interface CardView {
  player: Player
  name: string
  detail: string
  pips: number
  active: boolean
  tag: string
}

export interface ControlsView {
  /** Show Roll dice instead of Undo and Done */
  awaitingRoll: boolean
  canUndo: boolean
  canFinish: boolean
}

export type Tile = [number, string]

export interface ResultView {
  title: string
  won: boolean
  subtitle: string
  tiles: Tile[]
}

export interface GameModelOptions {
  config: GameConfig
  computerLevels: ComputerLevels
  session?: GameSession
  thinker?: Thinker
  stepDelayMs?: number
  showHints?: boolean
  /** The pause before the result shows, so the final position stays on screen for a moment */
  resultDelayMs?: number
}

export class GameModel {
  readonly session: GameSession
  readonly config: GameConfig
  readonly computerLevels: ComputerLevels
  showHints: boolean
  selected: number | null = null
  cursor: Target | null = null
  pauseOpen = false
  confirmingResign = false
  resultOpen = false
  lastStep: StepView | null = null
  private ai: AIController | null = null
  private thinker: Thinker | null = null
  private makeThinker: () => Thinker
  private stepDelayMs: number
  private attached = false
  private lastBoard: Board
  private stepCount = 0
  private resultTimer: ReturnType<typeof setTimeout> | null = null
  private resultDelayMs: number
  private listeners = new Set<() => void>()
  private version = 0

  constructor({ config, computerLevels, session, thinker, stepDelayMs = 500, showHints = true,
                resultDelayMs = 700 }: GameModelOptions) {
    this.config = config
    this.computerLevels = { ...computerLevels }
    this.session = session ?? new GameSession()
    this.showHints = showHints
    this.stepDelayMs = stepDelayMs
    this.resultDelayMs = resultDelayMs
    this.makeThinker = thinker !== undefined ? () => thinker : () => new WorkerThinker()
    this.lastBoard = copyBoard(this.session.board)
  }

  /** Attaches to the session and the computer players, and starts a game */
  start() {
    if (!this.attached) {
      this.attached = true
      this.session.addListener(this.onEvent)
      if (this.computerCount()) {
        this.thinker = this.makeThinker()
        this.ai = new AIController(this.session, this.computerLevels, this.thinker, { stepDelayMs: this.stepDelayMs })
      }
    }
    this.session.start()
  }

  /** Detaches from the session and ends the computer's thinking; the screen calls it when it goes away */
  stop() {
    if (!this.attached) return
    this.attached = false
    this.ai?.stop()
    this.thinker?.dispose?.()
    this.ai = null
    this.thinker = null
    this.session.removeListener(this.onEvent)
    if (this.resultTimer !== null) clearTimeout(this.resultTimer)
    this.resultTimer = null
  }

  // Rendering

  subscribe = (listener: () => void) => {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  getVersion = () => this.version

  private changed() {
    const tokens = this.candidates()
    if (!tokens.some((token) => sameTarget(token, this.cursor))) this.cursor = tokens[0] ?? null
    this.lastBoard = copyBoard(this.session.board)
    this.version += 1
    for (const listener of [...this.listeners]) listener()
  }

  // Players

  /** The player shown at the bottom: the human against the computer, otherwise white */
  bottomPlayer(): Player {
    const humans = ([1, -1] as Player[]).filter((p) => this.isHuman(p))
    return humans.length === 1 ? humans[0] : 1
  }

  isHuman(player: Player): boolean {
    return this.computerLevels[player] === undefined
  }

  private computerCount(): number {
    return Object.keys(this.computerLevels).length
  }

  playerName(player: Player): string {
    if (!this.isHuman(player)) return 'Computer'
    if (this.computerCount() === 1) return 'You'
    return player === 1 ? 'Player 1' : 'Player 2'
  }

  playerDetail(player: Player): string {
    const level = this.computerLevels[player]
    return level !== undefined ? `${COLOR_NAMES[player]}, ${capitalize(level)}` : COLOR_NAMES[player]
  }

  turnTag(player: Player): string {
    if (!this.isHuman(player)) return "Computer's turn"
    if (this.computerCount() === 1) return 'Your turn'
    return `${COLOR_NAMES[player]}'s turn`
  }

  // Actions

  humanTurn(): boolean {
    return !this.session.isOver() && this.isHuman(this.session.player) && !this.overlayOpen()
  }

  overlayOpen(): boolean {
    return this.pauseOpen || this.resultOpen
  }

  roll() {
    if (this.humanTurn()) this.session.roll()
  }

  undo() {
    if (!this.humanTurn()) return
    this.selected = null
    if (!this.session.undo()) this.changed()
  }

  done() {
    if (!this.humanTurn()) return
    this.selected = null
    if (!this.session.endTurn()) this.changed()
  }

  /** A click or tap on the board: picks a checker, moves the picked one, or bears it off */
  press(target: Target) {
    const session = this.session
    if (!this.humanTurn() || session.phase !== 'moving') return
    let [kind, point] = target
    if (kind === 'bar') {
      kind = 'point'
      point = barOf(session.player)
    }
    const sources = this.sources()
    if (kind === 'point' && point !== null) {
      if (this.selected === null) {
        if (sources.has(point)) this.selected = point
      } else if (point === this.selected) {
        this.selected = null
      } else if (this.targets().has(point)) {
        const start = this.selected
        this.selected = null
        session.move(start, Math.abs(point - start))
        return
      } else if (sources.has(point)) {
        this.selected = point
      }
    } else if (kind === 'tray' && this.selected !== null) {
      const jumps = this.bearOffJumps(this.selected)
      if (jumps.length) {
        const start = this.selected
        this.selected = null
        session.move(start, Math.min(...jumps))
        return
      }
    }
    this.changed()
  }

  /** Picks a checker, used when a drag starts on it */
  pick(point: number) {
    if (!this.humanTurn() || this.session.phase !== 'moving' || !this.sources().has(point)) return
    if (this.selected !== point) {
      this.selected = point
      this.changed()
    }
  }

  /** The end of a drag: moves the picked checker when it was dropped where it can go, otherwise it stays picked */
  drop(target: Target) {
    if (this.selected === null) return
    const [kind, point] = target
    if ((kind === 'point' && point !== null && this.targets().has(point))
        || (kind === 'tray' && this.bearOffJumps(this.selected).length)) {
      this.press(target)
    } else {
      this.changed()
    }
  }

  sources(): Set<number> {
    return new Set(this.session.legal.map(([start]) => start))
  }

  targets(): Set<number> {
    const targets = new Set<number>()
    if (this.selected === null) return targets
    for (const [start, jump] of this.session.legal) {
      if (start !== this.selected) continue
      const end = this.session.destination(start, jump)
      if (end !== null) targets.add(end)
    }
    return targets
  }

  private bearOffJumps(start: number): number[] {
    return this.session.legal
      .filter(([from, jump]) => from === start && this.session.destination(from, jump) === null)
      .map(([, jump]) => jump)
  }

  // Keyboard on the board

  /** What the keyboard cursor can stop on, in the player's direction of play: the movable
   * checkers, or once one is selected, the selected checker, its targets and the Off tray */
  candidates(): Target[] {
    const session = this.session
    if (!this.humanTurn() || session.phase !== 'moving') return []
    const bar = barOf(session.player)
    const token = (point: number): Target => (point === bar ? ['bar', null] : ['point', point])
    const order = (point: number) => (point === bar ? -1 : session.player === 1 ? point : 25 - point)
    const byOrder = (a: number, b: number) => order(a) - order(b)
    if (this.selected === null) return [...this.sources()].sort(byOrder).map(token)
    const tokens = [token(this.selected), ...[...this.targets()].sort(byOrder).map(token)]
    if (this.bearOffJumps(this.selected).length) tokens.push(['tray', null])
    return tokens
  }

  moveCursor(step: number) {
    const tokens = this.candidates()
    const index = tokens.findIndex((token) => sameTarget(token, this.cursor))
    if (!tokens.length) this.cursor = null
    else if (index < 0) this.cursor = tokens[0]
    else this.cursor = tokens[(index + step + tokens.length) % tokens.length]
    this.changed()
  }

  activateCursor() {
    if (this.cursor === null || !this.candidates().some((token) => sameTarget(token, this.cursor))) {
      this.moveCursor(0)
      return
    }
    this.press(this.cursor)
    if (this.selected !== null) {
      // Jump to the first place the selected checker can go
      const tokens = this.candidates()
      this.cursor = tokens.length > 1 ? tokens[1] : tokens[0]
    } else {
      this.cursor = null
    }
    this.changed()
  }

  /** Escape: drops the picked checker, or opens and closes the pause menu */
  cancelSelection() {
    if (this.selected !== null) {
      this.cursor = this.selected === barOf(this.session.player) ? ['bar', null] : ['point', this.selected]
      this.selected = null
      this.changed()
    } else if (this.confirmingResign) {
      this.cancelResign()
    } else if (this.pauseOpen) {
      this.closePause()
    } else {
      this.openPause()
    }
  }

  // Pause menu

  openPause() {
    if (this.overlayOpen() || this.session.isOver()) return
    this.ai?.pause()
    this.selected = null
    this.pauseOpen = true
    this.changed()
  }

  closePause() {
    this.pauseOpen = false
    this.confirmingResign = false
    this.ai?.resume()
    this.changed()
  }

  canResign(): boolean {
    return this.computerCount() < 2
  }

  /** Against the computer the human resigns, between friends the player whose turn it is */
  resigningPlayer(): Player {
    const humans = ([1, -1] as Player[]).filter((p) => this.isHuman(p))
    return humans.length === 1 ? humans[0] : this.session.player
  }

  askResign() {
    this.confirmingResign = true
    this.changed()
  }

  cancelResign() {
    this.confirmingResign = false
    this.changed()
  }

  resign(player: Player = this.resigningPlayer()) {
    this.pauseOpen = false
    this.confirmingResign = false
    this.session.resign(player)
    this.ai?.resume()
  }

  // Session events

  private onEvent = (event: SessionEvent) => {
    if (['game_started', 'turn_started', 'stepped', 'undone'].includes(event.type)) this.selected = null
    if (event.type === 'stepped') {
      this.stepCount += 1
      this.lastStep = {
        id: this.stepCount, before: this.lastBoard, after: copyBoard(this.session.board),
        player: event.player, start: event.start, end: event.end, hit: event.hit,
      }
    }
    if (event.type === 'game_started') this.resultOpen = false
    this.changed()
    if (event.type === 'game_over') {
      if (this.resultTimer !== null) clearTimeout(this.resultTimer)
      this.resultTimer = setTimeout(() => this.showResult(), this.session.stats.resigned ? 0 : this.resultDelayMs)
    }
  }

  private showResult() {
    this.resultTimer = null
    if (!this.session.isOver() || this.resultOpen) return
    this.resultOpen = true
    this.changed()
  }

  setPace(stepDelayMs: number) {
    this.stepDelayMs = stepDelayMs
    if (this.ai !== null) this.ai.stepDelayMs = stepDelayMs
  }

  // What the screen shows

  diceView(): DieView[] {
    const left = [...this.session.diceLeft]
    const view: DieView[] = []
    for (const value of [...this.session.dice].reverse()) {
      const index = left.indexOf(value)
      if (index >= 0) {
        left.splice(index, 1)
        view.push([value, false])
      } else {
        view.push([value, true])
      }
    }
    return view.reverse()
  }

  boardView(): BoardView {
    const session = this.session
    const moving = this.humanTurn() && session.phase === 'moving'
    const hints = moving && this.showHints
    const selected = moving ? this.selected : null
    return {
      board: session.board,
      dice: this.diceView(),
      sources: hints ? this.sources() : new Set(),
      pickable: moving ? this.sources() : new Set(),
      selected,
      targets: hints ? this.targets() : new Set(),
      trayTarget: hints && selected !== null && this.bearOffJumps(selected).length > 0,
      player: session.player,
      cursor: this.cursor,
    }
  }

  cards(): CardView[] {
    const session = this.session
    const bottom = this.bottomPlayer()
    return [-bottom as Player, bottom].map((player) => ({
      player,
      name: this.playerName(player),
      detail: this.playerDetail(player),
      pips: session.pips(player),
      active: !session.isOver() && player === session.player,
      tag: this.turnTag(player),
    }))
  }

  controls(): ControlsView {
    const human = this.humanTurn()
    return {
      awaitingRoll: human && this.session.phase === 'await_roll',
      canUndo: human && this.session.canUndo(),
      canFinish: human && this.session.phase === 'ready_to_end',
    }
  }

  hintCaption(): string {
    const session = this.session
    if (session.isOver()) return 'Game over'
    if (session.opening !== null) {
      const [white, black] = session.opening
      return `White rolled ${white}, black rolled ${black}`
    }
    if (session.phase === 'await_roll') return this.turnTag(session.player)
    const dice = new Set(session.dice).size > 1 ? session.dice.slice(0, 2).join(' and ') : `double ${session.dice[0]}`
    const who = this.playerName(session.player) === 'You' ? 'You'
      : !this.isHuman(session.player) ? 'The computer' : COLOR_NAMES[session.player]
    return `${who} rolled ${dice}`
  }

  /** verb is how the player presses: Click with a mouse, Tap on a touch screen */
  hintBody(verb: 'Click' | 'Tap' = 'Click'): string {
    const session = this.session
    if (session.isOver()) return `${COLOR_NAMES[session.stats.winner!]} won.`
    const starts = session.opening !== null ? `${COLOR_NAMES[session.player]} starts. ` : ''
    if (!this.isHuman(session.player)) {
      return starts + (session.phase === 'await_roll' ? 'Rolling the dice.' : 'Thinking and moving.')
    }
    if (session.phase === 'await_roll') return 'Roll the dice to start the turn.'
    if (session.phase === 'ready_to_end') {
      if (session.reason === NO_LEGAL_MOVES) {
        return starts + 'There is no legal move with these dice. Press Done to pass the turn.'
      }
      return 'All the dice you can play are used. Press Done to end the turn, or Undo to change it.'
    }
    if (this.selected !== null) {
      return starts + `${verb} a highlighted point to move there, or the checker again to cancel.`
    }
    return starts + 'Select a checker, then a highlighted point.'
  }

  resultView(): ResultView | null {
    const stats = this.session.stats
    if (stats.winner === null) return null
    const winner = stats.winner
    const loser = -winner as Player
    const turns = stats.turns + (stats.resigned ? 0 : 1)
    const how = stats.resigned ? 'by resignation' : `after ${turns} turns`
    const humans = ([1, -1] as Player[]).filter((p) => this.isHuman(p))
    if (humans.length === 1) {
      const human = humans[0]
      const won = winner === human
      const level = capitalize(this.computerLevels[-human as Player]!)
      return {
        title: won ? 'You won' : 'You lost',
        won,
        subtitle: `against the computer on ${level}, ${how}`,
        tiles: [[turns, 'turns'], [stats.hits[human], 'hits by you'],
                [this.session.pips(loser), won ? 'computer pips left' : 'your pips left']],
      }
    }
    const won = humans.length === 2
    const names = { winner: this.playerName(winner), loser: this.playerName(loser) }
    return {
      title: `${COLOR_NAMES[winner]} won`,
      won,
      subtitle: won ? `${names.winner} beat ${names.loser}, ${how}` : `Computer against computer, ${how}`,
      tiles: [[turns, 'turns'], [stats.hits[winner], `hits by ${COLOR_NAMES[winner].toLowerCase()}`],
              [this.session.pips(loser), `${COLOR_NAMES[loser].toLowerCase()} pips left`]],
    }
  }
}
