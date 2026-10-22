import logging
import random
import time

from ai.evaluators import HeuristicEvaluator
from ai.move_gen import full_moves
from ai.search import choose_move

log = logging.getLogger(__name__)

# Looking at the opponent's replies (depth 2) only made the computer stronger with the trained network,
# with the hand written evaluation it played as well as depth 1, so hard uses the network.
LEVELS = {
    'easy': {'depth': 1, 'temperature': 0.05, 'time_limit': None, 'evaluator': 'heuristic'},
    'medium': {'depth': 1, 'temperature': 0.0, 'time_limit': None, 'evaluator': 'heuristic'},
    'hard': {'depth': 2, 'temperature': 0.0, 'time_limit': 2.5, 'evaluator': 'td'},
}


def load_evaluator(name):
    """The evaluator a level asks for, the hand written one when the network can not be loaded"""
    if name == 'td':
        try:
            from ai.td import TDEvaluator
            evaluator = TDEvaluator.load()
        except ImportError:
            evaluator = None
        if evaluator is not None:
            return evaluator
        log.warning('the trained network is not available, using the hand written evaluation')
    return HeuristicEvaluator()


class ComputerPlayer:
    def __init__(self, level='medium', evaluator=None, rng=None):
        self.level = level
        self.settings = LEVELS[level]
        self.evaluator = evaluator or load_evaluator(self.settings['evaluator'])
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
