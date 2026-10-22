# Backgammon

Backgammon built with PyQt6, for two players or against the computer.

## Run

```
pip install -r requirements.txt
python main.py
```

A dialog at startup chooses the mode: two players, against the computer (choose its color and level)
or computer against computer.

Click a highlighted checker to select it, then click a highlighted point to move it.
When a checker can be borne off, the brown area on the right is highlighted.

## Computer player

The code is in `ai/`:

- `move_gen.py` lists every full move for a roll, using the rules in `rules.py`
- `evaluators.py` estimates the chance of winning from a position
- `search.py` picks the move: 1-ply evaluates every move, 2-ply also averages over all the opponent rolls
  and stops at a time limit
- `ai_controller.py` plays for the computer in the gui, thinking in a background thread

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
