# Backgammon

Backgammon built with PyQt6, for two players or against the computer.

## Run

```
pip install -r requirements.txt
python main.py
```

The game opens on the home screen. New game chooses the opponent (the computer at easy, medium or hard,
or a friend on this computer) and your color (white, black or random).

Settings (show legal moves, computer move speed, default level and color) and the New game choices are saved
with QSettings. Statistics (wins, losses, win rate and streak per level, and games with a friend) are saved
in `stats.json` in the user's application data folder. Resigning or leaving a game against the computer counts
as a loss.

During a game the menu button or Escape opens the pause menu: resume, restart with the same setup, settings, resign,
or go back to the main menu (which ends the game). When the game ends, the result shows over the board with
a short summary and Rematch, New game or Main menu.

The look follows the Midnight Felt design system in `DESIGN.md`; `ui/theme.py` holds the same tokens and
a test keeps the two in sync. The Outfit and Inter fonts are bundled in `assets/fonts` under the SIL Open Font License.

## Playing

The first player is decided by an opening roll: each side rolls one die and the higher one moves first
with both dice. After that each turn is:

1. Roll dice (R).
2. Click a highlighted checker, then a highlighted point. To bear off, click the Off tray on the right.
   Click the checker again to cancel. Checkers slide to their new point, a hit checker slides to the bar.
3. Undo (Ctrl+Z or U) takes back moves until the turn ends.
4. Done (D) ends the turn once every die that can be played is used. When no move is possible
   the board says so and Done passes the turn.

The board can also be played with the keyboard: Tab to it, the arrow keys move a dashed cursor over the
checkers you can move (or, once one is picked, over its targets and the Off tray), Enter or Space picks,
and Escape cancels the pick. Escape with nothing picked opens the pause menu.

## Code

- `rules.py`: the rules as pure functions over a board
- `game/config.py`: the setup chosen on the New game screen
- `game/session.py`: one game as a turn state machine (opening roll, roll, move, undo, end turn, resign),
  no gui; listeners get every change as an event
- `stores/`: saved settings and statistics
- `ui/`: the PyQt window, the screens, the board widget (`ui/board`) and the theme
- `ai/`: the computer player

## Computer player

The code is in `ai/`:

- `move_gen.py` lists every full move for a roll, using the rules in `rules.py`
- `evaluators.py` estimates the chance of winning from a position
- `search.py` picks the move: 1-ply evaluates every move, 2-ply also averages over all the opponent rolls
  and stops at a time limit
- `ai_controller.py` plays for the computer through the game session: it rolls, thinks in a background thread,
  plays the steps one by one and ends the turn

Levels:

- easy: 1-ply with the hand written evaluation and some randomness
- medium: 1-ply with the hand written evaluation
- hard: 2-ply with the trained network in `ai/weights/td.npz`, up to 2.5 seconds per move

The network is a TD-Gammon style network trained by playing against itself:

```
python -m ai.train_td 20000
```

Compare players without the gui:

```
python -m ai.bench 200 hard medium
python -m ai.bench 200 td:medium medium   # td:<level> runs a level with the network
```

## Tests

```
python -m unittest discover -s tests
```
