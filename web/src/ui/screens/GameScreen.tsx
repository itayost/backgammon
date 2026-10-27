import { useEffect, useState, useSyncExternalStore } from 'react'
import type { Thinker } from '../../ai/thinker'
import type { ComputerLevels, GameConfig } from '../../game/config'
import { Board } from '../board/Board'
import { GameModel, type CardView, type ControlsView, type ResultView } from '../gameModel'
import { Button, CheckerDot, Dialog, IconButton } from '../widgets'

export interface GameSetup {
  /** A new id starts a new game, also with the same config */
  id: number
  config: GameConfig
  computerLevels: ComputerLevels
}

interface GameScreenProps {
  setup: GameSetup
  onRestart(): void
  onNewGame(): void
  stepDelayMs?: number
  showHints?: boolean
  /** For tests: think without a worker */
  thinker?: Thinker
}

const coarsePointer = () => typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches

export function GameScreen({ setup, onRestart, onNewGame, stepDelayMs = 500, showHints = true, thinker }: GameScreenProps) {
  const [model] = useState(() => new GameModel({
    config: setup.config, computerLevels: setup.computerLevels, stepDelayMs, showHints, thinker,
  }))
  useSyncExternalStore(model.subscribe, model.getVersion)

  useEffect(() => {
    model.start()
    return () => model.stop()
  }, [model])

  // The turn keys are letters, so Space and Enter stay with the focused button or the board
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.altKey || event.defaultPrevented) return
      const key = event.key.toLowerCase()
      const command = event.ctrlKey || event.metaKey
      if (command && key === 'z') model.undo()
      else if (command) return
      else if (key === 'r') model.roll()
      else if (key === 'u') model.undo()
      else if (key === 'd') model.done()
      else if (key === 'escape') model.cancelSelection()
      else return
      event.preventDefault()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [model])

  const [top, bottom] = model.cards()
  const overlay = model.overlayOpen()
  const result = model.resultOpen ? model.resultView() : null

  return (
    <div className="game">
      <div className="game-layout" inert={overlay}>
        <header className="game-header">
          <span className="wordmark">Backgammon</span>
          <IconButton icon="menu" label="Menu" onClick={() => model.openPause()} />
        </header>
        <PlayerCard card={top} area="top" />
        <div className="game-board">
          <Board
            view={model.boardView()}
            step={model.lastStep}
            onPress={(target) => model.press(target)}
            onPick={(point) => model.pick(point)}
            onDrop={(target) => model.drop(target)}
            onNavigate={(step) => model.moveCursor(step)}
            onActivate={() => model.activateCursor()}
            onCancel={() => model.cancelSelection()}
          />
          <p id="board-help" className="visually-hidden">
            Arrow keys choose a checker or a point, Enter picks it, Escape cancels.
            Keys: R rolls the dice, U undoes a move, D ends the turn.
          </p>
        </div>
        <PlayerCard card={bottom} area="bottom" />
        <section className="hint" aria-live="polite">
          <p className="caption">{model.hintCaption()}</p>
          <p className="hint-text">{model.hintBody(coarsePointer() ? 'Tap' : 'Click')}</p>
        </section>
        <TurnControls controls={model.controls()} model={model} />
      </div>

      {model.pauseOpen && <PauseDialog model={model} onRestart={onRestart} onNewGame={onNewGame} />}
      {result !== null && <ResultDialog result={result} onRematch={onRestart} onNewGame={onNewGame} />}
    </div>
  )
}

function PlayerCard({ card, area }: { card: CardView; area: 'top' | 'bottom' }) {
  return (
    <section className={`player-card ${area}${card.active ? ' active' : ''}`} aria-label={`${card.name}, ${card.detail}`}>
      <CheckerDot player={card.player} size={36} />
      <div className="player-names">
        <span className="label">{card.name}</span>
        <span className="muted">{card.detail}</span>
      </div>
      {card.active && <span className="tag">{card.tag}</span>}
      <div className="pips">
        <span className="number">{card.pips}</span>
        <span className="muted">pips</span>
      </div>
    </section>
  )
}

function TurnControls({ controls, model }: { controls: ControlsView; model: GameModel }) {
  return (
    <div className="turn-controls">
      {controls.awaitingRoll ? (
        <Button variant="primary" size="large" className="roll" onClick={() => model.roll()}>Roll dice</Button>
      ) : (
        <>
          <Button size="large" disabled={!controls.canUndo} onClick={() => model.undo()}>Undo</Button>
          <Button variant="primary" size="large" disabled={!controls.canFinish} onClick={() => model.done()}>Done</Button>
        </>
      )}
    </div>
  )
}

function PauseDialog({ model, onRestart, onNewGame }: { model: GameModel; onRestart(): void; onNewGame(): void }) {
  if (model.confirmingResign) {
    const color = model.resigningPlayer() === 1 ? 'white' : 'black'
    return (
      <Dialog labelledBy="resign-title">
        <h2 id="resign-title" className="headline">Resign?</h2>
        <p className="muted">Resign this game as {color}? The other side wins.</p>
        <div className="dialog-actions">
          <Button variant="danger" size="large" onClick={() => model.resign()}>Resign</Button>
          <Button size="large" onClick={() => model.cancelResign()}>Keep playing</Button>
        </div>
      </Dialog>
    )
  }
  return (
    <Dialog labelledBy="pause-title">
      <h2 id="pause-title" className="headline">Paused</h2>
      <div className="dialog-actions">
        <Button variant="primary" size="large" onClick={() => model.closePause()}>Resume</Button>
        <Button size="large" onClick={onRestart}>Restart with the same setup</Button>
        {model.canResign() && <Button variant="danger" size="large" onClick={() => model.askResign()}>Resign</Button>}
      </div>
      <hr className="divider" />
      <Button variant="ghost" onClick={onNewGame}>New game</Button>
      <p className="muted center">Leaving ends this game.</p>
    </Dialog>
  )
}

function ResultDialog({ result, onRematch, onNewGame }: { result: ResultView; onRematch(): void; onNewGame(): void }) {
  return (
    <Dialog labelledBy="result-title" wide>
      <div className="result-head">
        <h2 id="result-title" className={`display${result.won ? ' won' : ''}`}>{result.title}</h2>
        <p className="muted">{result.subtitle}</p>
      </div>
      <div className="tiles">
        {result.tiles.map(([value, caption]) => (
          <div key={caption} className="tile">
            <span className="number">{value}</span>
            <span className="muted">{caption}</span>
          </div>
        ))}
      </div>
      <div className="dialog-actions">
        <Button variant="primary" size="large" onClick={onRematch}>Rematch</Button>
        <Button size="large" onClick={onNewGame}>New game</Button>
      </div>
    </Dialog>
  )
}
