/** The Game screen without a browser: ports of the GameScreen, overlay and keyboard tests in tests/test_ui.py */
import { afterEach, describe, expect, test, vi } from 'vitest'
import type { Thinker } from '../src/ai/thinker'
import { computerLevels, type ComputerLevels, type GameConfig } from '../src/game/config'
import type { Board, Player } from '../src/game/rules'
import { geometry } from '../src/ui/board/geometry'
import { slidesFor } from '../src/ui/board/slides'
import { GameModel } from '../src/ui/gameModel'
import { emptyBoard } from './helpers'

/** A computer that never answers, for tests that only need it to be there */
const silent: Thinker = { think: () => new Promise(() => {}), cancel: () => {} }

const models: GameModel[] = []

/** A started game with the opening roll 5 and 3: white moves first with both dice */
function game(levels: ComputerLevels = {}, config: GameConfig = { opponent: 'friend', level: 'easy', color: 'white' }) {
  const model = new GameModel({ config, computerLevels: levels, thinker: silent, resultDelayMs: 0 })
  models.push(model)
  model.start()
  model.session.start([5, 3])
  return model
}

/** Puts the session on a custom board at the start of a turn and rolls the dice */
function rollOn(model: GameModel, board: Board, player: Player, dice: number[]) {
  model.session.board = board
  model.session.player = player
  model.session.phase = 'await_roll'
  model.session.roll(dice)
}

afterEach(() => {
  for (const model of models.splice(0)) model.stop()
  vi.useRealTimers()
})

describe('game config', () => {
  test('the computer plays the other color', () => {
    expect(computerLevels({ opponent: 'friend', level: 'easy', color: 'white' })).toEqual({})
    expect(computerLevels({ opponent: 'computer', level: 'hard', color: 'white' })).toEqual({ [-1]: 'hard' })
    expect(computerLevels({ opponent: 'computer', level: 'easy', color: 'black' })).toEqual({ 1: 'easy' })
    expect(computerLevels({ opponent: 'self_play', level: 'medium', color: 'white' })).toEqual({ 1: 'medium', [-1]: 'medium' })
    const drawn = new Set([0.1, 0.9].map((r) => Object.keys(computerLevels({ opponent: 'computer', level: 'easy', color: 'random' }, () => r))[0]))
    expect(drawn).toEqual(new Set(['1', '-1']))
  })
})

describe('pressing the board', () => {
  test('select, then move', () => {
    const model = game()
    model.press(['point', 17])
    expect(model.selected).toBe(17)
    expect(model.boardView().targets).toEqual(new Set([20, 22]))
    model.press(['point', 22])
    expect(model.session.board[22]).toEqual([1, 1])
    expect(model.selected).toBeNull()
    expect(model.session.diceLeft).toEqual([3])
  })

  test('pressing the picked checker again drops it', () => {
    const model = game()
    model.press(['point', 17])
    model.press(['point', 17])
    expect(model.selected).toBeNull()
  })

  test('pressing another checker that can move picks it instead', () => {
    const model = game()
    model.press(['point', 17])
    model.press(['point', 12])
    expect(model.selected).toBe(12)
  })

  test('the buttons follow the turn', () => {
    const model = game()
    expect(model.controls()).toEqual({ awaitingRoll: false, canUndo: false, canFinish: false })
    model.press(['point', 17])
    model.press(['point', 22])
    expect(model.controls().canUndo).toBe(true)
    model.press(['point', 19])
    model.press(['point', 22])
    expect(model.controls().canFinish).toBe(true)
    model.undo()
    expect(model.controls().canFinish).toBe(false)
    model.press(['point', 19])
    model.press(['point', 22])
    model.done()
    expect(model.session.player).toBe(-1)
    expect(model.controls().awaitingRoll).toBe(true)
    model.roll()
    expect(model.controls().awaitingRoll).toBe(false)
  })

  test('bear off through the tray', () => {
    const model = game()
    const board = emptyBoard()
    board[22] = [2, 1]
    board[3] = [2, -1]
    rollOn(model, board, 1, [6, 2])
    model.press(['point', 22])
    expect(model.boardView().trayTarget).toBe(true)
    model.press(['tray', null])
    expect(model.session.board[22]).toEqual([1, 1])
    expect(model.session.diceLeft).toEqual([2])
  })

  test("the computer's turn ignores presses", () => {
    const model = game({ 1: 'easy' })
    model.press(['point', 17])
    expect(model.selected).toBeNull()
    expect(model.boardView().sources).toEqual(new Set())
    expect(model.boardView().pickable).toEqual(new Set())
  })

  test('a drag moves only where the checker can go', () => {
    const model = game()
    model.pick(17)
    expect(model.selected).toBe(17)
    model.drop(['point', 21])
    expect(model.selected).toBe(17)
    expect(model.session.board[21]).toEqual([0, 0])
    model.drop(['point', 20])
    expect(model.session.board[20]).toEqual([1, 1])
  })

  test('without hints nothing is marked, but checkers still move', () => {
    const model = new GameModel({ config: { opponent: 'friend', level: 'easy', color: 'white' }, computerLevels: {}, showHints: false })
    models.push(model)
    model.start()
    model.session.start([5, 3])
    model.press(['point', 17])
    const view = model.boardView()
    expect([view.sources.size, view.targets.size, view.pickable.size > 0]).toEqual([0, 0, true])
    model.press(['point', 22])
    expect(model.session.board[22]).toEqual([1, 1])
  })
})

describe('the pause menu and the result', () => {
  test('pause freezes the game', () => {
    const model = game({ [-1]: 'easy' })
    model.openPause()
    expect(model.pauseOpen).toBe(true)
    model.press(['point', 17])
    expect(model.selected).toBeNull()
    expect(model.boardView().sources).toEqual(new Set())
    model.closePause()
    model.press(['point', 17])
    expect(model.selected).toBe(17)
  })

  test('Escape drops the picked checker, then opens and closes the pause menu', () => {
    const model = game()
    model.press(['point', 17])
    model.cancelSelection()
    expect(model.selected).toBeNull()
    expect(model.pauseOpen).toBe(false)
    model.cancelSelection()
    expect(model.pauseOpen).toBe(true)
    model.cancelSelection()
    expect(model.pauseOpen).toBe(false)
  })

  test('resigning shows the loss', async () => {
    vi.useFakeTimers()
    const model = game({ [-1]: 'easy' })
    model.openPause()
    model.askResign()
    expect(model.confirmingResign).toBe(true)
    model.resign()
    expect(model.pauseOpen).toBe(false)
    await vi.advanceTimersByTimeAsync(0)
    expect(model.resultOpen).toBe(true)
    const result = model.resultView()!
    expect([result.title, result.won]).toEqual(['You lost', false])
    expect(result.subtitle).toContain('by resignation')
    expect(result.subtitle).toContain('on Easy')
  })

  test('the summary of a win', () => {
    const model = game({ [-1]: 'easy' })
    const board = emptyBoard()
    board[24] = [1, 1]
    board[5] = [3, -1]
    rollOn(model, board, 1, [6, 3])
    model.session.move(24, 6)
    const result = model.resultView()!
    expect([result.title, result.won]).toEqual(['You won', true])
    expect(result.tiles[2]).toEqual([15, 'computer pips left'])
  })

  test('the result waits a moment so the last move stays on screen', async () => {
    vi.useFakeTimers()
    const model = new GameModel({ config: { opponent: 'friend', level: 'easy', color: 'white' }, computerLevels: {} })
    models.push(model)
    model.start()
    const board = emptyBoard()
    board[24] = [1, 1]
    board[5] = [3, -1]
    rollOn(model, board, 1, [6, 3])
    model.session.move(24, 6)
    expect(model.resultOpen).toBe(false)
    await vi.advanceTimersByTimeAsync(700)
    expect(model.resultOpen).toBe(true)
    expect(model.resultView()!.title).toBe('White won')
  })

  test('no resigning between computers', () => {
    expect(game({ 1: 'easy', [-1]: 'easy' }).canResign()).toBe(false)
  })
})

describe('the texts of the turn', () => {
  test('the opening roll and who starts', () => {
    const model = game()
    expect(model.hintCaption()).toBe('White rolled 5, black rolled 3')
    expect(model.hintBody()).toBe('White starts. Select a checker, then a highlighted point.')
    model.press(['point', 17])
    expect(model.hintBody('Tap')).toBe('White starts. Tap a highlighted point to move there, or the checker again to cancel.')
  })

  test('the players are named after who plays them', () => {
    const vsComputer = game({ [-1]: 'hard' })
    expect(vsComputer.cards().map((card) => [card.name, card.detail])).toEqual([['Computer', 'Black, Hard'], ['You', 'White']])
    expect(vsComputer.cards()[1].tag).toBe('Your turn')
    const friends = game()
    expect(friends.cards().map((card) => card.name)).toEqual(['Player 2', 'Player 1'])
    expect(friends.cards()[1].tag).toBe("White's turn")
  })
})

describe('slides and the keyboard', () => {
  const g = geometry(904, 692)

  test('a move slides from where the checker stood', () => {
    const model = game()
    model.press(['point', 17])
    model.press(['point', 22])
    const slides = slidesFor(g, model.session.board, model.lastStep)
    expect([...slides.points.keys()]).toEqual([22])
    expect(slides.bars.size).toBe(0)
  })

  test('a hit checker slides to the bar', () => {
    const model = game()
    const board = model.session.board
    board[20] = [1, -1]
    board[13] = [4, -1]
    rollOn(model, board, 1, [5, 3])
    model.press(['point', 17])
    model.press(['point', 20])
    const slides = slidesFor(g, model.session.board, model.lastStep)
    expect([...slides.points.keys()]).toEqual([20])
    expect([...slides.bars.keys()]).toEqual([-1])
  })

  test('a new position ends the slide', () => {
    const model = game()
    model.press(['point', 17])
    model.press(['point', 22])
    model.undo()
    expect(slidesFor(g, model.session.board, model.lastStep).points.size).toBe(0)
  })

  test('the keyboard moves a checker', () => {
    const model = game()
    model.moveCursor(1)
    expect(model.cursor).toEqual(['point', 12])
    model.moveCursor(-1)
    model.moveCursor(-1)
    expect(model.cursor).toEqual(['point', 19])
    model.moveCursor(-1)
    expect(model.cursor).toEqual(['point', 17])
    model.activateCursor()
    expect(model.selected).toBe(17)
    expect(model.cursor).toEqual(['point', 20])
    model.moveCursor(1)
    model.activateCursor()
    expect(model.session.board[22]).toEqual([1, 1])
    expect(model.selected).toBeNull()
  })

  test('the keyboard bears off through the tray', () => {
    const model = game()
    const board = emptyBoard()
    board[22] = [2, 1]
    board[3] = [2, -1]
    rollOn(model, board, 1, [6, 2])
    model.activateCursor()
    expect(model.candidates()).toEqual([['point', 22], ['point', 24], ['tray', null]])
    model.moveCursor(1)
    model.activateCursor()
    expect(model.session.board[22]).toEqual([1, 1])
    expect(model.session.diceLeft).toEqual([2])
  })

  test('the bar comes first', () => {
    const model = game()
    const board = model.session.board
    board[0] = [1, 1]
    board[1] = [1, 1]
    rollOn(model, board, 1, [5, 3])
    expect(model.candidates()).toEqual([['bar', null]])
    model.activateCursor()
    expect(model.selected).toBe(0)
  })
})
