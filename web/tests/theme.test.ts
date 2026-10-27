/** The web tokens must match DESIGN.md, like tests/test_theme.py does for the desktop theme */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, test } from 'vitest'

const read = (path: string) => readFileSync(fileURLToPath(new URL(path, import.meta.url)), 'utf-8')
const design = read('../../DESIGN.md').split('---')[1]
const tokens = read('../src/styles/tokens.css')

/** The key: value lines of one top level section of the DESIGN.md frontmatter */
function section(name: string): Record<string, string> {
  const block = new RegExp(`^${name}:\\n((?:  .*\\n)+)`, 'm').exec(design)![1]
  return Object.fromEntries([...block.matchAll(/^ {2}([\w-]+): (.+)$/gm)].map(([, key, value]) => [key, value.replace(/"/g, '')]))
}

function token(name: string): string | undefined {
  return new RegExp(`--${name}: ([^;]+);`).exec(tokens)?.[1]
}

describe('tokens.css matches DESIGN.md', () => {
  test('colors', () => {
    const colors = section('colors')
    expect(Object.keys(colors).length).toBeGreaterThan(20)
    for (const [name, value] of Object.entries(colors)) expect(token(`color-${name}`), name).toBe(value)
  })

  test('radius', () => {
    for (const [name, value] of Object.entries(section('rounded'))) expect(token(`rounded-${name}`), name).toBe(value)
  })

  test('spacing', () => {
    for (const [name, value] of Object.entries(section('spacing'))) expect(token(name), name).toBe(value)
  })

  test('font families', () => {
    const typography = /^typography:\n((?: {2,}.*\n)+)/m.exec(design)![1]
    const families = new Set([...typography.matchAll(/fontFamily: "([^"]+)"/g)].map(([, family]) => family))
    expect(families).toEqual(new Set([token('font-display'), token('font-body')]))
  })
})
