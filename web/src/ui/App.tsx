import { useState } from 'react'
import { DEFAULT_CONFIG, computerLevels, type GameConfig } from '../game/config'
import { GameScreen, type GameSetup } from './screens/GameScreen'
import { NewGameScreen } from './screens/NewGameScreen'

type Screen = { name: 'new_game' } | { name: 'game'; setup: GameSetup }

let nextGame = 1

function setupFor(config: GameConfig): GameSetup {
  return { id: nextGame++, config, computerLevels: computerLevels(config) }
}

export function App() {
  const [config, setConfig] = useState<GameConfig>(DEFAULT_CONFIG)
  const [screen, setScreen] = useState<Screen>({ name: 'new_game' })

  if (screen.name === 'game') {
    return (
      <GameScreen
        key={screen.setup.id}
        setup={screen.setup}
        // A rematch draws a random color again, like a new game with the same choices
        onRestart={() => setScreen({ name: 'game', setup: setupFor(screen.setup.config) })}
        onNewGame={() => setScreen({ name: 'new_game' })}
      />
    )
  }
  return (
    <NewGameScreen
      initial={config}
      onStart={(chosen) => {
        setConfig(chosen)
        setScreen({ name: 'game', setup: setupFor(chosen) })
      }}
    />
  )
}
