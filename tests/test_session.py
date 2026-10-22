import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import rules  # noqa: E402
from game.session import GameSession, Phase, NO_LEGAL_MOVES  # noqa: E402


def empty_board():
    board = [[0, 0] for _ in range(26)]
    board[0] = [0, 1]
    board[25] = [0, -1]
    return board


class SequenceRng:
    """Returns the given dice values in order"""

    def __init__(self, values):
        self.values = list(values)

    def randint(self, low, high):
        return self.values.pop(0)


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.session = GameSession(random.Random(1))
        self.events = []
        self.session.add_listener(lambda event, data: self.events.append((event, data)))

    def at_roll(self, board, player):
        """Puts the session at the start of a turn on a custom board"""
        self.session.board = board
        self.session.player = player
        self.session.phase = Phase.AWAIT_ROLL

    def test_opening_roll_starts_the_higher_die(self):
        self.session.start(opening=(3, 5))
        self.assertEqual(self.session.player, -1)
        self.assertEqual(self.session.dice, [3, 5])
        self.assertEqual(self.session.phase, Phase.MOVING)
        self.assertEqual(self.session.opening, (3, 5))

    def test_opening_roll_repeats_ties(self):
        session = GameSession(SequenceRng([4, 4, 2, 2, 6, 1]))
        session.start()
        self.assertEqual(session.opening, (6, 1))
        self.assertEqual(session.player, 1)

    def test_roll_only_when_waiting(self):
        self.session.start(opening=(6, 1))
        self.assertFalse(self.session.roll([3, 4]))

    def test_illegal_move_is_rejected(self):
        self.session.start(opening=(6, 1))
        self.assertFalse(self.session.move(1, 4))
        self.assertFalse(self.session.move(6, 1))

    def test_turn_needs_done(self):
        self.session.start(opening=(3, 1))
        self.assertTrue(self.session.move(17, 3))
        self.assertTrue(self.session.move(19, 1))
        self.assertEqual(self.session.phase, Phase.READY_TO_END)
        self.assertIsNone(self.session.reason)
        self.assertEqual(self.session.player, 1)
        self.assertTrue(self.session.end_turn())
        self.assertEqual(self.session.player, -1)
        self.assertEqual(self.session.phase, Phase.AWAIT_ROLL)
        self.assertEqual(self.session.stats.turns, 1)
        self.assertEqual(self.events[-1], ('turn_started', {'player': -1}))

    def test_end_turn_only_when_ready(self):
        self.session.start(opening=(3, 1))
        self.assertFalse(self.session.end_turn())

    def test_undo_restores_a_hit(self):
        board = empty_board()
        board[1] = [2, 1]
        board[4] = [1, -1]
        board[20] = [2, -1]
        self.at_roll(board, 1)
        self.session.roll([3, 6])
        self.assertTrue(self.session.move(1, 3))
        self.assertEqual(self.session.board[25], [1, -1])
        self.assertEqual(self.session.stats.hits[1], 1)
        self.assertTrue(self.session.undo())
        self.assertEqual(self.session.board[4], [1, -1])
        self.assertEqual(self.session.board[25][0], 0)
        self.assertEqual(self.session.stats.hits[1], 0)
        self.assertEqual(sorted(self.session.dice_left), [3, 6])
        self.assertEqual(self.session.phase, Phase.MOVING)

    def test_undo_from_ready_and_nothing_to_undo(self):
        self.session.start(opening=(3, 1))
        self.assertFalse(self.session.undo())
        self.session.move(17, 3)
        self.session.move(19, 1)
        self.assertTrue(self.session.undo())
        self.assertEqual(self.session.phase, Phase.MOVING)
        self.assertEqual(self.session.dice_left, [1])

    def test_no_legal_moves_waits_for_done(self):
        board = empty_board()
        board[0] = [1, 1]
        for i in range(1, 7):
            board[i] = [2, -1]
        board[24] = [14, 1]
        self.at_roll(board, 1)
        self.session.roll([3, 4])
        self.assertEqual(self.session.phase, Phase.READY_TO_END)
        self.assertEqual(self.session.reason, NO_LEGAL_MOVES)
        self.assertTrue(self.session.end_turn())
        self.assertEqual(self.session.player, -1)

    def test_bar_checker_must_enter_first(self):
        board = rules.init_board()
        board[0] = [1, 1]
        board[1] = [1, 1]
        self.at_roll(board, 1)
        self.session.roll([3, 5])
        self.assertTrue(all(position == 0 for position, _ in self.session.legal))

    def test_white_wins_by_bearing_off(self):
        board = empty_board()
        board[24] = [1, 1]
        board[5] = [3, -1]
        self.at_roll(board, 1)
        self.session.roll([6, 3])
        self.assertTrue(self.session.move(24, 6))
        self.assertEqual(self.session.phase, Phase.GAME_OVER)
        self.assertEqual(self.session.stats.winner, 1)
        self.assertEqual(self.events[-1], ('game_over', {'winner': 1}))

    def test_black_wins_by_bearing_off(self):
        board = empty_board()
        board[2] = [1, -1]
        board[20] = [3, 1]
        self.at_roll(board, -1)
        self.session.roll([2, 1])
        self.assertTrue(self.session.move(2, 2))
        self.assertEqual(self.session.stats.winner, -1)
        self.assertFalse(self.session.undo())

    def test_resign(self):
        self.session.start(opening=(3, 1))
        self.assertTrue(self.session.resign(1))
        self.assertEqual(self.session.stats.winner, -1)
        self.assertTrue(self.session.stats.resigned)
        self.assertFalse(self.session.resign(1))

    def test_pips_at_start(self):
        self.session.start(opening=(3, 1))
        self.assertEqual(self.session.pips(1), 167)
        self.assertEqual(self.session.pips(-1), 167)

    def test_events_of_a_move(self):
        self.session.start(opening=(3, 1))
        self.events.clear()
        self.session.move(17, 3)
        self.assertEqual([event for event, _ in self.events], ['stepped', 'turn_changed'])
        self.assertEqual(self.events[0][1], {'player': 1, 'start': 17, 'end': 20, 'hit': False})

    def test_random_games_finish_with_legal_states(self):
        rng = random.Random(3)
        for _ in range(20):
            self.session.start()
            while self.session.phase != Phase.GAME_OVER:
                if self.session.phase == Phase.AWAIT_ROLL:
                    self.session.roll()
                elif self.session.phase == Phase.MOVING:
                    if rng.random() < 0.1 and self.session.can_undo():
                        self.session.undo()
                    else:
                        self.session.move(*rng.choice(self.session.legal))
                else:
                    self.session.end_turn()
                for count, owner in self.session.board:
                    self.assertGreaterEqual(count, 0)
                    if count:
                        self.assertIn(owner, (1, -1))
                for player in (1, -1):
                    self.assertLessEqual(rules.checkers_left(self.session.board, player), 15)
            self.assertEqual(rules.checkers_left(self.session.board, self.session.stats.winner), 0)


if __name__ == '__main__':
    unittest.main()
