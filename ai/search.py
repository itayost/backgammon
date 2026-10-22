import math
import random
import time

import rules
from ai.move_gen import full_moves, all_rolls

# How many of the best 1-ply candidates are checked with the deeper search
CANDIDATES = 8


def values_for(boards, player, player_to_move, evaluator):
    """Winning probability of every board from the point of view of player"""
    values = evaluator.evaluate(boards, player_to_move)
    result = []
    for board, value in zip(boards, values):
        if rules.checkers_left(board, 1) == 0:
            value = 1.0
        elif rules.checkers_left(board, -1) == 0:
            value = 0.0
        result.append(value if player == 1 else 1 - value)
    return result


def expected_after_reply(board, player, evaluator, deadline):
    """The average over all the opponent rolls of the position after its best reply,
    or None when the deadline passed before the calculation ended"""
    if rules.checkers_left(board, player) == 0:
        return 1.0
    opponent = -player
    total = 0.0
    for dice, probability in all_rolls():
        if deadline is not None and time.monotonic() > deadline:
            return None
        replies = [reply for reply, _ in full_moves(board, opponent, dice)]
        total += probability * min(values_for(replies, player, player, evaluator))
    return total


def choose_move(board, player, dice, evaluator, depth=1, deadline=None, temperature=0.0, rng=random):
    """The steps of the move to play, an empty list when there is no legal move.
    depth 2 looks at every opponent roll, and stops at the deadline keeping the 1-ply choice
    for the candidates it did not reach. temperature above 0 adds randomness for easier play."""
    options = full_moves(board, player, dice)
    if len(options) == 1:
        return options[0][1]

    scores = values_for([option for option, _ in options], player, -player, evaluator)
    order = sorted(range(len(options)), key=lambda i: scores[i], reverse=True)

    if temperature > 0:
        weights = [math.exp((scores[i] - scores[order[0]]) / temperature) for i in range(len(options))]
        return options[rng.choices(range(len(options)), weights=weights)[0]][1]

    best = order[0]
    if depth >= 2:
        best_score = None
        for i in order[:CANDIDATES]:
            score = expected_after_reply(options[i][0], player, evaluator, deadline)
            if score is None:
                break
            if best_score is None or score > best_score:
                best, best_score = i, score
    return options[best][1]
