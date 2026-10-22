import os
import random
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import rules  # noqa: E402
from ai.bench import bench  # noqa: E402
from ai.evaluators import HeuristicEvaluator  # noqa: E402
from ai.move_gen import full_moves, all_rolls, board_key  # noqa: E402
from ai.player import ComputerPlayer  # noqa: E402
from ai.search import choose_move  # noqa: E402


def empty_board():
    board = [[0, 0] for _ in range(26)]
    board[0] = [0, 1]
    board[25] = [0, -1]
    return board


def play(board, player, dice, steps):
    board = rules.copy_board(board)
    dice = list(dice)
    for position, jump in steps:
        assert (position, jump) in rules.possible_moves(board, player, dice)
        rules.apply_move(board, player, position, jump)
        dice.remove(jump)
    return board, dice


class MoveGenTest(unittest.TestCase):
    def test_rolls_cover_all_probability(self):
        rolls = all_rolls()
        self.assertEqual(len(rolls), 21)
        self.assertAlmostEqual(sum(p for _, p in rolls), 1.0)

    def test_full_moves_are_legal_and_distinct(self):
        rng = random.Random(1)
        board, player = rules.init_board(), 1
        for _ in range(40):
            dice = rules.roll_dice()
            options = full_moves(board, player, dice)
            keys = [board_key(b) for b, _ in options]
            self.assertEqual(len(keys), len(set(keys)))
            for result, steps in options:
                played, left = play(board, player, dice, steps)
                self.assertEqual(board_key(played), board_key(result))
                if rules.checkers_left(played, player):
                    self.assertEqual(rules.possible_moves(played, player, left), [])
            board = rng.choice(options)[0]
            if rules.checkers_left(board, player) == 0:
                break
            player = -player

    def test_no_moves_keeps_board(self):
        board = empty_board()
        board[0] = [1, 1]
        for i in range(1, 7):
            board[i] = [2, -1]
        options = full_moves(board, 1, [3, 4])
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0][1], [])

    def test_does_not_change_the_input_board(self):
        board = rules.init_board()
        full_moves(board, 1, [6, 6, 6, 6])
        self.assertEqual(board, rules.init_board())


class EvaluatorTest(unittest.TestCase):
    def test_race_leader_is_favourite(self):
        board = empty_board()
        board[22] = [15, 1]
        board[10] = [15, -1]
        value = HeuristicEvaluator().evaluate_one(board, 1)
        self.assertGreater(value, 0.9)

    def test_blot_in_front_of_opponent_is_worse(self):
        safe = rules.init_board()
        exposed = rules.copy_board(safe)
        rules.apply_move(exposed, 1, 1, 4)  # white leaves a blot on 1 and on 5, in front of black's 6 and 8
        evaluator = HeuristicEvaluator()
        self.assertLess(evaluator.evaluate_one(exposed, -1), evaluator.evaluate_one(safe, -1))


class SearchTest(unittest.TestCase):
    def test_hits_a_free_blot(self):
        board = empty_board()
        board[2] = [1, 1]
        board[19] = [7, 1]
        board[20] = [7, 1]
        board[5] = [1, -1]
        board[3] = [14, -1]
        steps = choose_move(board, 1, [3, 1], HeuristicEvaluator())
        result, _ = play(board, 1, [3, 1], steps)
        self.assertEqual(result[25][0], 1)

    def test_takes_a_checker_off_when_possible(self):
        board = empty_board()
        board[24] = [1, 1]
        board[5] = [3, -1]
        steps = choose_move(board, 1, [6, 1], HeuristicEvaluator(), depth=2)
        result, _ = play(board, 1, [6, 1], steps)
        self.assertEqual(rules.checkers_left(result, 1), 0)

    def test_deep_search_respects_deadline(self):
        board = rules.init_board()
        start = time.monotonic()
        steps = choose_move(board, 1, [3, 3, 3, 3], HeuristicEvaluator(), depth=2, deadline=start + 0.2)
        self.assertLess(time.monotonic() - start, 1.0)
        play(board, 1, [3, 3, 3, 3], steps)

    def test_every_level_returns_legal_moves(self):
        rng = random.Random(2)
        for level in ('easy', 'medium', 'hard'):
            computer = ComputerPlayer(level, rng=random.Random(0))
            board, player = rules.init_board(), 1
            for _ in range(6):
                dice = rules.roll_dice()
                board, left = play(board, player, dice, computer.choose(board, player, dice))
                self.assertEqual(rules.possible_moves(board, player, left), [])
                board = rng.choice(full_moves(board, -player, rules.roll_dice()))[0]


class LevelTest(unittest.TestCase):
    def test_hard_uses_the_trained_network(self):
        from ai.td import TDEvaluator
        self.assertIsInstance(ComputerPlayer('hard').evaluator, TDEvaluator)

    def test_falls_back_without_the_network(self):
        from unittest import mock
        with mock.patch('ai.td.TDEvaluator.load', return_value=None):
            self.assertIsInstance(ComputerPlayer('hard').evaluator, HeuristicEvaluator)

    def test_network_scores_are_probabilities(self):
        from ai.td import TDEvaluator
        values = TDEvaluator.load().evaluate([rules.init_board()], 1)
        self.assertTrue(0 <= values[0] <= 1)


class StrengthTest(unittest.TestCase):
    def test_medium_beats_random(self):
        rate, _, _ = bench(30, 'medium', 'random', seed=7)
        self.assertGreaterEqual(rate, 0.8)


if __name__ == '__main__':
    unittest.main()
