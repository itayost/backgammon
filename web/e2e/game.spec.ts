import { expect, test, type Locator, type Page } from '@playwright/test'

/** Presses the middle of an element on the board: a tap on touch screens, a click elsewhere */
async function press(page: Page, element: Locator) {
  const box = (await element.boundingBox())!
  const [x, y] = [box.x + box.width / 2, box.y + box.height / 2]
  if (test.info().project.use.hasTouch) await page.touchscreen.tap(x, y)
  else await page.mouse.click(x, y)
}

const board = (page: Page) => page.getByRole('application', { name: 'Backgammon board' })
const movable = (page: Page) => board(page).locator('[data-movable]')
const targets = (page: Page) => board(page).locator('[data-target]')
const button = (page: Page, name: string) => page.getByRole('button', { name, exact: true })

async function startGame(page: Page, opponent: 'Computer' | 'Friend on this device') {
  await page.goto('/')
  await page.getByRole('radio', { name: new RegExp(opponent) }).click()
  await button(page, 'Start game').click()
  await expect(board(page)).toBeVisible()
}

/** Plays one die: picks the first checker that can move and puts it on its first target */
async function playOneDie(page: Page) {
  await press(page, movable(page).first())
  await expect(targets(page).first()).toBeAttached()
  await press(page, targets(page).first())
}

/** Rolls when needed, plays every die that can be played and ends the turn */
async function playTurn(page: Page) {
  if (await button(page, 'Roll dice').isVisible()) await button(page, 'Roll dice').click()
  for (let die = 0; die < 4 && !(await button(page, 'Done').isEnabled()); die++) await playOneDie(page)
  await expect(button(page, 'Done')).toBeEnabled()
  await button(page, 'Done').click()
}

test('a friend game: move, undo and end the turn', async ({ page }) => {
  await startGame(page, 'Friend on this device')
  // The opening roll decides who starts, and that player moves with both dice at once
  const caption = page.locator('.hint .caption')
  await expect(caption).toHaveText(/White rolled \d, black rolled \d/)
  const starter = (await page.locator('.hint-text').textContent())!.startsWith('White') ? 'White' : 'Black'

  await expect(button(page, 'Undo')).toBeDisabled()
  await playOneDie(page)
  await expect(button(page, 'Undo')).toBeEnabled()
  await button(page, 'Undo').click()
  await expect(button(page, 'Undo')).toBeDisabled()

  await playTurn(page)
  const next = starter === 'White' ? 'Black' : 'White'
  await expect(caption).toHaveText(`${next}'s turn`)
  await expect(button(page, 'Roll dice')).toBeVisible()
  await playTurn(page)
  await expect(caption).toHaveText(`${starter}'s turn`)
})

test('the computer answers', async ({ page }) => {
  await startGame(page, 'Computer')
  const you = page.locator('.player-card.bottom')
  // Whoever starts, after the computer's turn it is yours again
  await expect(button(page, 'Roll dice').or(button(page, 'Done'))).toBeVisible()
  for (let turn = 0; turn < 2; turn++) {
    await expect(you).toHaveClass(/active/, { timeout: 20_000 })
    await expect(movable(page).first().or(button(page, 'Roll dice'))).toBeVisible()
    await playTurn(page)
    await expect(page.locator('.player-card.top')).toHaveClass(/active/)
  }
  await expect(you).toHaveClass(/active/, { timeout: 20_000 })
})

test('pause, resign and rematch', async ({ page }) => {
  await startGame(page, 'Computer')
  await button(page, 'Menu').click()
  const pause = page.getByRole('dialog', { name: 'Paused' })
  await expect(pause).toBeVisible()
  await expect(button(page, 'Resume')).toBeFocused()
  await button(page, 'Resign').click()
  await page.getByRole('dialog', { name: 'Resign?' }).getByRole('button', { name: 'Resign' }).click()

  const result = page.getByRole('dialog', { name: 'You lost' })
  await expect(result).toBeVisible()
  await expect(result).toContainText('by resignation')
  await button(page, 'Rematch').click()
  await expect(result).toBeHidden()
  await expect(page.locator('.hint .caption')).toHaveText(/rolled/)
})

test('Escape opens and closes the pause menu', async ({ page }) => {
  test.skip(test.info().project.use.hasTouch === true, 'keyboard')
  await startGame(page, 'Friend on this device')
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog', { name: 'Paused' })).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog', { name: 'Paused' })).toBeHidden()
})

test('keyboard play on the board', async ({ page }) => {
  test.skip(test.info().project.use.hasTouch === true, 'keyboard')
  await startGame(page, 'Friend on this device')
  await board(page).focus()
  // Enter picks the checker under the cursor and moves the cursor to its first target, Enter again moves it
  await page.keyboard.press('ArrowRight')
  await page.keyboard.press('Enter')
  await expect(targets(page).first()).toBeAttached()
  await page.keyboard.press('Enter')
  await expect(button(page, 'Undo')).toBeEnabled()
  await page.keyboard.press('u')
  await expect(button(page, 'Undo')).toBeDisabled()
})

test('drag a checker to where it can go', async ({ page }) => {
  test.skip(test.info().project.use.hasTouch === true, 'mouse drag')
  await startGame(page, 'Friend on this device')
  const from = (await movable(page).first().boundingBox())!
  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2)
  await page.mouse.down()
  const to = (await targets(page).first().boundingBox())!
  await page.mouse.move(to.x + to.width / 2, to.y + to.height / 2, { steps: 8 })
  await page.mouse.up()
  await expect(button(page, 'Undo')).toBeEnabled()
})

test('drag a checker with a finger', async ({ page }) => {
  test.skip(test.info().project.use.hasTouch !== true, 'touch drag')
  await startGame(page, 'Friend on this device')
  const center = async (element: Locator) => {
    const box = (await element.boundingBox())!
    return { x: box.x + box.width / 2, y: box.y + box.height / 2 }
  }
  // Real touch events through the DevTools protocol; Playwright's touchscreen only taps
  const cdp = await page.context().newCDPSession(page)
  const from = await center(movable(page).first())
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [from] })
  await expect(targets(page).first()).toBeAttached()
  const to = await center(targets(page).first())
  for (let i = 1; i <= 8; i++) {
    const point = { x: from.x + ((to.x - from.x) * i) / 8, y: from.y + ((to.y - from.y) * i) / 8 }
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [point] })
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await expect(button(page, 'Undo')).toBeEnabled()
})

test('the board and the controls fit on the screen', async ({ page }) => {
  await startGame(page, 'Computer')
  const viewport = page.viewportSize()!
  const area = (await board(page).boundingBox())!
  expect(area.x).toBeGreaterThanOrEqual(0)
  expect(area.y).toBeGreaterThanOrEqual(0)
  expect(area.x + area.width).toBeLessThanOrEqual(viewport.width)
  expect(area.y + area.height).toBeLessThanOrEqual(viewport.height)
  const controls = (await page.locator('.turn-controls').boundingBox())!
  expect(controls.y + controls.height).toBeLessThanOrEqual(viewport.height)
  // Nothing scrolls sideways
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(viewport.width)
})

test('the start button is within reach without scrolling', async ({ page }) => {
  await page.goto('/')
  const start = (await button(page, 'Start game').boundingBox())!
  expect(start.y + start.height).toBeLessThanOrEqual(page.viewportSize()!.height)
})
