import { useState } from 'react'
import { capitalize, type ColorChoice, type GameConfig, type Level, type Opponent } from '../../game/config'
import { Button, ChoiceGroup, IconButton, SegmentedControl } from '../widgets'

const LEVEL_TEXT: Record<Level, string> = {
  easy: 'Plays sensible moves with some randomness. Good for learning.',
  medium: 'Picks the best move it can see for each roll.',
  hard: 'Also looks at every reply you could roll. Thinks up to 2.5 seconds.',
}

interface NewGameScreenProps {
  initial: GameConfig
  onStart(config: GameConfig): void
  onBack?: () => void
}

export function NewGameScreen({ initial, onStart, onBack }: NewGameScreenProps) {
  const [config, setConfig] = useState<GameConfig>({
    ...initial, opponent: initial.opponent === 'self_play' ? 'computer' : initial.opponent,
  })
  const update = (changes: Partial<GameConfig>) => setConfig({ ...config, ...changes })

  const vsComputer = config.opponent === 'computer'
  const me = vsComputer ? 'You' : 'Player 1'
  const other = vsComputer ? `Computer, ${capitalize(config.level)}` : 'Player 2'
  const [white, black] = config.color === 'random' ? ['Drawn at random', 'Drawn at random']
    : config.color === 'white' ? [me, other] : [other, me]

  return (
    <main className="screen new-game" onKeyDown={(event) => event.key === 'Escape' && onBack?.()}>
      <header className="screen-header">
        {onBack && <IconButton icon="back" label="Back" onClick={onBack} />}
        <h1 className="headline">New game</h1>
      </header>

      <div className="new-game-columns">
        <div className="new-game-choices">
          <section className="card" aria-labelledby="opponent-title">
            <h2 id="opponent-title" className="title">Opponent</h2>
            <ChoiceGroup<Opponent>
              label="Opponent"
              className="opponents"
              value={config.opponent}
              onChange={(opponent) => update({ opponent })}
              options={[
                { label: 'Computer', value: 'computer', text: 'Play against the computer at the level you choose.' },
                { label: 'Friend on this device', value: 'friend', text: 'Two players take turns on the same board.' },
              ]}
            />
          </section>

          {vsComputer && (
            <section className="card" aria-labelledby="level-title">
              <h2 id="level-title" className="title">Level</h2>
              <SegmentedControl<Level>
                label="Level"
                value={config.level}
                onChange={(level) => update({ level })}
                options={[['Easy', 'easy'], ['Medium', 'medium'], ['Hard', 'hard']]}
              />
              <p className="muted">{LEVEL_TEXT[config.level]}</p>
            </section>
          )}

          <section className="card" aria-labelledby="color-title">
            <h2 id="color-title" className="title">{vsComputer ? 'Your color' : 'Player 1 color'}</h2>
            <ChoiceGroup<ColorChoice>
              label="Color"
              className="colors"
              value={config.color}
              onChange={(color) => update({ color })}
              options={[
                { label: 'White', value: 'white', player: 1 },
                { label: 'Black', value: 'black', player: -1 },
                { label: 'Random', value: 'random', player: null },
              ]}
            />
          </section>
        </div>

        <aside className="card summary" aria-label="Summary">
          <p className="caption">Summary</p>
          <dl className="summary-rows">
            <dt className="muted">White</dt><dd className="label">{white}</dd>
            <dt className="muted">Black</dt><dd className="label">{black}</dd>
            <dt className="muted">First move</dt><dd className="label">Opening roll</dd>
          </dl>
          <p className="muted">Each side rolls one die; the higher die moves first with both dice.</p>
          <div className="start-dock">
            <Button variant="primary" size="large" className="start" onClick={() => onStart(config)}>Start game</Button>
          </div>
        </aside>
      </div>
    </main>
  )
}
