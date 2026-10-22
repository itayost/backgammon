import random
import time

from ai.evaluators import HeuristicEvaluator
from ai.move_gen import full_moves
from ai.search import choose_move

LEVELS = {
    'easy': {'depth': 1, 'temperature': 0.05, 'time_limit': None},
    'medium': {'depth': 1, 'temperature': 0.0, 'time_limit': None},
    'hard': {'depth': 2, 'temperature': 0.0, 'time_limit': 2.5},
}


class ComputerPlayer:
    def __init__(self, level='medium', evaluator=None, rng=None):
        self.level = level
        self.settings = LEVELS[level]
        self.evaluator = evaluator or HeuristicEvaluator()
        self.rng = rng or random.Random()

    def choose(self, board, player, dice):
        """The steps (position, jump) to play for this roll"""
        limit = self.settings['time_limit']
        deadline = time.monotonic() + limit if limit is not None else None
        return choose_move(board, player, dice, self.evaluator, depth=self.settings['depth'],
                           deadline=deadline, temperature=self.settings['temperature'], rng=self.rng)


class RandomPlayer:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()

    def choose(self, board, player, dice):
        return self.rng.choice(full_moves(board, player, dice))[1]
