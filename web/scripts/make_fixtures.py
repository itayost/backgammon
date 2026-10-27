"""Writes web/tests/fixtures/parity.json: positions from seeded random games with what the Python code
says about them (legal moves, the steps to every reachable position, the evaluations and the moves the
levels choose).
web/tests/parity.test.ts checks that the TypeScript port says the same.

Run from the repository root after changing the rules or the computer player:
    python web/scripts/make_fixtures.py
"""
import json
import os
import random
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

import rules  # noqa: E402
from ai.evaluators import HeuristicEvaluator  # noqa: E402
from ai.move_gen import full_moves  # noqa: E402
from ai.search import choose_move  # noqa: E402
from ai.td import TDEvaluator  # noqa: E402

TARGET = os.path.join(ROOT, 'web', 'tests', 'fixtures', 'parity.json')
GAMES = 12
EVERY = 3           # keep every third position of a game
HARD_EVERY = 6      # and run the slow 2-ply search on every sixth kept position
RARE = 25           # positions for each rule that random games seldom reach


def sample_positions(rng):
    """(board, player, dice) along random games, with checkers on the bar and bearing off included"""
    positions = []
    for _ in range(GAMES):
        board, player = rules.init_board(), rng.choice([1, -1])
        turn = 0
        while rules.checkers_left(board, 1) and rules.checkers_left(board, -1):
            dice = rules.roll_dice_with(rng)
            if turn % EVERY == 0:
                positions.append((rules.copy_board(board), player, dice))
            board = rng.choice(full_moves(board, player, dice))[0]
            player = -player
            turn += 1
    return positions


def higher_die_rule_applies(board, player, dice):
    """Only one of two different dice can be played, and the lower one could be played on its own"""
    if len(set(dice)) != 2 or rules.max_dice_used(board, player, dice) != 1:
        return False
    return any(jump == min(dice) for _, jump in rules.single_moves(board, player, dice))


def partly_playable(board, player, dice):
    return 0 < rules.max_dice_used(board, player, dice) < len(dice)


def rare_positions(rng, wanted=RARE):
    """Positions that random sampling seldom keeps: the higher die rule and dice that can be played only in part"""
    found = {higher_die_rule_applies: [], partly_playable: []}
    while any(len(positions) < wanted for positions in found.values()):
        board, player = rules.init_board(), rng.choice([1, -1])
        while rules.checkers_left(board, 1) and rules.checkers_left(board, -1):
            dice = rules.roll_dice_with(rng)
            for test, positions in found.items():
                if len(positions) < wanted and test(board, player, dice):
                    positions.append((rules.copy_board(board), player, dice))
            board = rng.choice(full_moves(board, player, dice))[0]
            player = -player
    return [position for positions in found.values() for position in positions]


def main():
    rng = random.Random(2024)
    heuristic = HeuristicEvaluator()
    td = TDEvaluator.load()
    fixtures = []
    for index, (board, player, dice) in enumerate(sample_positions(rng) + rare_positions(rng)):
        options = full_moves(board, player, dice)
        fixtures.append({
            'board': board,
            'player': player,
            'dice': dice,
            'legal': [list(move) for move in rules.possible_moves(board, player, dice)],
            'full': [[list(step) for step in steps] for _, steps in options],
            'heuristic': [heuristic.evaluate_one(board, 1), heuristic.evaluate_one(board, -1)],
            'td': [td.evaluate([board], 1)[0], td.evaluate([board], -1)[0]],
            'medium': [list(step) for step in choose_move(board, player, dice, heuristic)],
            'hard': [list(step) for step in choose_move(board, player, dice, td, depth=2)]
            if index % HARD_EVERY == 0 else None,
        })
    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    with open(TARGET, 'w') as f:
        json.dump({'positions': fixtures}, f, separators=(',', ':'))
        f.write('\n')
    hard = sum(1 for fixture in fixtures if fixture['hard'] is not None)
    print(f'wrote {os.path.relpath(TARGET, ROOT)}: {len(fixtures)} positions, {hard} with the 2-ply search')


if __name__ == '__main__':
    main()
