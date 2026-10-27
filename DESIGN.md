---
name: Backgammon
description: A desktop backgammon game for two players or against the computer, played on a lit board at a dark table.
colors:
  bg: "#0E1617"
  surface: "#162224"
  surface-2: "#1E2E30"
  line: "#2C4144"
  text: "#EEE7D9"
  text-muted: "#9DB0AD"
  text-disabled: "#6F8380"
  accent: "#F0A73A"
  accent-hover: "#F5BC66"
  accent-ink: "#1A1206"
  danger: "#F08A7E"
  danger-surface: "#2A1A19"
  danger-line: "#5A2A26"
  success: "#8FD3A8"
  board-frame: "#3B2A1E"
  board-bar: "#2E2016"
  board-felt: "#1F4A44"
  point-light: "#D9CDB4"
  point-dark: "#A8473A"
  checker-white: "#F4EFE4"
  checker-white-rim: "#C9BFAE"
  checker-black: "#1C1C1E"
  checker-black-rim: "#4A4A50"
  scrim: "rgba(5, 10, 11, 0.72)"
typography:
  display:
    fontFamily: "Outfit, system-ui, sans-serif"
    fontSize: "56px"
    fontWeight: 700
    lineHeight: "64px"
  headline:
    fontFamily: "Outfit, system-ui, sans-serif"
    fontSize: "32px"
    fontWeight: 600
    lineHeight: "40px"
  title:
    fontFamily: "Outfit, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: "28px"
  number:
    fontFamily: "Outfit, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: "32px"
    fontFeature: "tnum"
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "24px"
  label:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "20px"
  caption:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: "16px"
    letterSpacing: "0.08em"
rounded:
  sm: "6px"
  segment: "8px"
  md: "10px"
  choice: "12px"
  lg: "16px"
  pill: "999px"
spacing:
  space-1: "4px"
  space-2: "8px"
  space-3: "12px"
  space-4: "16px"
  space-5: "24px"
  space-6: "32px"
  space-7: "48px"
  space-8: "64px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.accent-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.accent-ink}"
  button-secondary:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "48px"
  button-ghost:
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "48px"
  button-danger:
    backgroundColor: "{colors.danger-surface}"
    textColor: "{colors.danger}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "48px"
  button-disabled:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text-disabled}"
    rounded: "{rounded.md}"
    height: "48px"
  icon-button:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    size: "44px"
  segment:
    textColor: "{colors.text-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.segment}"
    padding: "0 20px"
    height: "40px"
  segment-selected:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.accent-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.segment}"
    padding: "0 20px"
    height: "40px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "24px"
  dialog:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "32px"
    width: "400px"
  checker-white:
    backgroundColor: "{colors.checker-white}"
    rounded: "{rounded.pill}"
    size: "50px"
  checker-black:
    backgroundColor: "{colors.checker-black}"
    rounded: "{rounded.pill}"
    size: "50px"
  die:
    backgroundColor: "{colors.checker-white}"
    textColor: "{colors.accent-ink}"
    rounded: "{rounded.md}"
    size: "48px"
---

# Design System: Backgammon

## Overview

**Creative North Star: "Midnight Felt"**

A late-night game table. The room is dark and calm, a deep ink-teal that recedes, and the board sits in the middle of it like the only lit object: a walnut frame, teal felt, bone and oxblood points, checkers with real weight. Everything around the board is quiet so the decisions on it carry the weight.

One warm color does all the talking. Amber marks what the player can act on right now: the primary button, the selected checker, the points a checker can legally reach, the active player. When amber appears, it is an invitation. Everything else stays in the ink and bone range.

The interface is a desktop game window, not a website. Controls are solid and tactile: firm 48 px buttons, filled states, clear disabled states. Panels are flat and separated by tone; only physical objects (the board, checkers, dice) and modal dialogs cast shadows.

**Key Characteristics:**
- Dark ink-teal room, warm lit board as the focal point
- A single amber accent reserved for actionable and active things
- Outfit for anything that is read at a glance (titles, numbers), Inter for everything that is read in full
- Flat panels, lifted physical pieces
- Generous 44 to 56 px hit targets everywhere, including the board

## Colors

A cool, dark room with a warm board and one amber signal.

### Primary
- **Lamp Amber** (accent): the only accent. Primary buttons, the selected segment, the selected checker's ring, legal target points and landing spots, the active player's card border, step numbers. Hover lightens to **Amber Glow** (accent-hover). Text on amber is always **Amber Ink** (accent-ink).

### Neutral
- **Midnight Ink** (bg): the app background on every screen.
- **Table Slate** (surface): cards, panels, dialogs.
- **Raised Slate** (surface-2): secondary buttons, icon buttons, choice cards, stat tiles inside a card.
- **Felt Seam** (line): 1 px borders and dividers between rows.
- **Bone Text** (text): primary text and numbers.
- **Sage Mist** (text-muted): secondary text, captions, descriptions, unselected segments.
- **Faded Sage** (text-disabled): disabled controls only.
- **Night Scrim** (scrim): the overlay behind pause and game-over dialogs, so the board stays visible but out of play.

### Board
- **Walnut** (board-frame) and **Dark Walnut** (board-bar): the frame, the bar and the bear-off tray.
- **Deep Felt** (board-felt): the playing field.
- **Bone Point** (point-light) and **Oxblood Point** (point-dark): alternating points.
- **Ivory** and **Onyx** checkers (checker-white, checker-black), each with a rim one step darker or lighter (checker-white-rim, checker-black-rim) so stacks stay readable.

### Feedback
- **Ember** (danger) on **Ember Surface** (danger-surface) with an **Ember Seam** border (danger-line): Resign and Reset statistics. Destructive actions only.
- **Win Green** (success): the "You won" headline and the winner's ring. Never used for buttons.

### Named Rules
**The One Lamp Rule.** Amber means "you can act on this" or "this is active". Never use it for decoration, headings, links that do nothing, or a losing state.

**The Board Owns The Warmth Rule.** Warm colors (walnut, bone, oxblood, amber) belong to the board and to actions. App chrome stays in the cool ink and sage range.

## Typography

**Display Font:** Outfit (with system-ui, sans-serif)
**Body Font:** Inter (with system-ui, sans-serif)

**Character:** Outfit is geometric and confident, used for what the eye grabs in a glance: screen titles, the winner, pip counts. Inter carries every sentence and label, and stays legible at 12 to 16 px.

### Hierarchy
- **Display** (700, 56px/64px): the result on the game-over dialog, the token sheet title. The home screen wordmark is the one larger exception (80px/84px).
- **Headline** (600, 32px/40px): screen titles (New game, Settings, Paused).
- **Title** (600, 22px/28px): card and section titles inside a screen.
- **Number** (600, 28px/32px, tabular figures): pip counts, statistics, game-over figures. Large stat tiles may go up to 44px.
- **Body** (400, 16px/24px): button labels and running text. Descriptions in cards use 14px/20px.
- **Label** (500, 14px/20px): setting names, segment labels, form labels.
- **Caption** (600, 12px/16px, +0.08em, uppercase): section kickers, table headers, the "Your turn" tag.

### Named Rules
**The Glance Rule.** If the player reads it in under a second (a title, a number, a result), it is Outfit. If they read it as a sentence, it is Inter.

**The Tabular Numbers Rule.** Every number that can change during play uses tabular figures, so pip counts and statistics do not jitter.

## Layout

The window is designed at 1280 by 800 px, with 24 px outer padding on the game screen and 40 by 96 px on menu screens.

- **Game screen:** a 44 px header (wordmark, menu button), then the board (904 by 692 px) beside a 304 px side panel, 24 px apart. The panel stacks the opponent card, the current player card, a hint card, flexible space, and the turn controls at the bottom.
- **Menu screens:** a header row with a 44 px back button and the screen title, then content in one or two columns of cards with 20 to 24 px gaps.
- **Home:** a two column composition, the wordmark and a 320 px menu on the left, a decorative board fragment on the right.
- **Dialogs:** centered over the scrim, 400 to 480 px wide.
- **Spacing rhythm:** 4, 8, 12, 16, 24, 32, 48, 64 px. Inside cards 24 px padding; between related controls 12 px; between sections 24 to 28 px.

### Web and phones

The web app (`web/`) keeps this layout on wide screens and adapts it, rather than scaling it, on phones:

- **Phone held upright:** one column. The opponent's card above the board, the player's card below it, then the hint and the turn controls at the bottom, within reach of the thumb. The board takes the full width and may grow taller than the desktop proportions (down to 0.8 wide for 1 tall) so the points stay long enough to touch.
- **Wide screens and phones on their side:** the board beside the side panel. When the height is short the header moves into the panel and the cards and hint get tighter.
- **The board** is drawn for the size it gets, not scaled from 904 by 692: frame, bar and tray get thinner on small boards, and checkers fill their point's width. A point owns its whole half column for presses, and on touch screens a press next to a highlighted point counts as on it.
- **Player cards on narrow layouts** carry the turn tag on their top edge, so the names keep the whole width.
- **New game on a phone:** one column, and Start game stays docked at the bottom of the screen.
- Hover states only apply where the device can hover; touch gets a pressed state instead.

## Elevation & Depth

Flat UI, lifted board. Panels, cards and buttons are flat and separated by tone (ink, slate, raised slate) and 1 px seams. Shadows are reserved for physical objects and for dialogs that float above the game.

### Shadow Vocabulary
- **Piece** (`box-shadow: 0 2px 6px rgba(0,0,0,0.35)`): checkers and the small dice in the token sheet.
- **Thrown die** (`box-shadow: 0 4px 10px rgba(0,0,0,0.4)`): dice on the board.
- **Board and dialog** (`box-shadow: 0 16px 40px rgba(0,0,0,0.55)`): the board frame and modal dialogs.

### Named Rules
**The Only Physical Things Cast Shadows Rule.** If you could pick it up off a real table (board, checker, die) or it floats over the game (a dialog), it has a shadow. Cards and panels never do.

## Shapes

Softly rounded rectangles for all chrome, true circles for checkers, and the triangle for points.

- Small radius (6px) for the board bar and tray, medium (10px) for buttons and dice, 12px for choice cards and the segmented control's track, 16px for cards and dialogs, pill (999px) for checkers, switches and tags.
- Points are drawn as triangles clipped from the felt, pointing toward the center of the board.
- Borders are 1 px Felt Seam on cards, 2 px for selectable cards (Felt Seam at rest, Lamp Amber when selected).

## Components

### Buttons
Solid and tactile: firm, filled, unmistakable.
- **Shape:** gently rounded (10px), 48 px tall (52 to 56 px for the main action of a screen), 24 px horizontal padding.
- **Primary:** Lamp Amber fill, Amber Ink text, weight 600. One per screen or dialog.
- **Hover / Focus:** hover lightens to Amber Glow. Keyboard focus is a 2 px amber ring offset by 2 px on every control.
- **Secondary:** Raised Slate fill with a 1 px Felt Seam border, Bone Text.
- **Ghost:** no fill, Bone Text, weight 500, for low priority exits (Quit, Main menu).
- **Danger:** Ember Surface fill, Ember Seam border, Ember text, for Resign and Reset statistics.
- **Disabled:** Raised Slate fill, Faded Sage text, no border.

### Icon buttons
44 by 44 px, Raised Slate with a Felt Seam border, a 20 px stroke icon. Used for Back and the in-game menu. Always carries an accessible name.

### Segmented control
A Midnight Ink track (12px radius, 4 px inner padding) with 40 px segments (8px radius). The selected segment is filled Lamp Amber with Amber Ink text; others are Sage Mist text on the track. Used for level, speed and color choices.

### Switch
52 by 30 px pill. On: Lamp Amber track with an Amber Ink knob on the right. Off: Felt Seam track with a Sage Mist knob on the left. Announced as a switch with its setting name.

### Cards / Containers
- **Corner Style:** 16px.
- **Background:** Table Slate, with Raised Slate for tiles nested inside.
- **Shadow Strategy:** none (see Elevation & Depth).
- **Border:** 1 px Felt Seam; selectable cards use 2 px, amber when selected.
- **Internal Padding:** 24 px (16 px for player cards).

### Player card
Checker swatch (36 px), name and role ("Computer", "Black, Medium"), and the pip count in Number style on the right. The active player's card has a 2 px Lamp Amber border and an amber "Your turn" pill tag.

### Board
The signature component. Walnut frame (16px radius, 14 px padding) holding two felt fields, the bar between them and the bear-off tray on the right. Each field is two rows of six points. Checkers are 50 px and stack toward the center; above five, the top checker shows the count. Legal targets turn the point Lamp Amber and show a dashed landing ring; the selected checker gets a 3 px amber ring. Dice sit in the middle of the right field and fade to 35% once used.

### Turn controls
At the bottom of the side panel. Before the roll: one full width primary "Roll dice". While moving: secondary "Undo" and a disabled "Done". When every playable die is used: "Done" turns primary.

### Dialogs
Table Slate, 16px radius, 32 px padding, the board and dialog shadow, over the Night Scrim. Title in Headline style, actions stacked full width, primary first, the destructive action separated from the exit by a seam.

## Do's and Don'ts

### Do:
- **Do** keep amber for actionable or active elements only (The One Lamp Rule).
- **Do** keep every interactive element at least 44 by 44 px, including points and checkers on the board.
- **Do** use tabular figures for pip counts, statistics and anything that updates during play.
- **Do** show the board behind pause and game-over dialogs, dimmed by the Night Scrim, so the player never loses context.
- **Do** give every control a visible 2 px amber focus ring for keyboard play.

### Don't:
- **Don't** put shadows on cards or panels; only physical pieces and dialogs are lifted.
- **Don't** use green for buttons or anything except a win.
- **Don't** introduce a second accent color; new states are expressed with tone, borders or amber.
- **Don't** use warm colors in app chrome; walnut, bone and oxblood belong to the board.
- **Don't** use gradients, glows or decorative textures on the felt or the chrome.
