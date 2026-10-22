import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backgammon import backgammon  # noqa: E402


def empty_board():
    board = [[0, 0] for _ in range(26)]
    board[0] = [0, 1]
    board[25] = [0, -1]
    return board


class FakeController:
    def __init__(self):
        self.events = []

    def to_gui_new_game(self, board):
        self.events.append(('new_game',))

    def to_gui_new_move(self, moves_made, moves_available, dice):
        self.events.append(('move', moves_made))

    def to_gui_throw_made(self, position, moves_available, dice):
        self.events.append(('throw', position))

    def to_gui_new_turn(self, player, dice, moves):
        self.events.append(('new_turn', player))

    def to_gui_winner(self, player):
        self.events.append(('winner', player))

    def to_gui_no_moves(self, player, dice):
        self.events.append(('no_moves', player))


class BackgammonTest(unittest.TestCase):
    def setUp(self):
        self.game = backgammon()
        self.controller = FakeController()
        self.game.list_of_controllers.append(self.controller)

    def set_state(self, board, player, dice):
        self.game.board = board
        self.game.current_player = player
        self.game.dice = list(dice)
        self.game.moves = self.game.possible_moves(board, player, self.game.dice)

    def test_initial_board_has_15_checkers_each(self):
        board = self.game.init_board()
        self.assertEqual(sum(c[0] for c in board if c[1] == 1), 15)
        self.assertEqual(sum(c[0] for c in board if c[1] == -1), 15)

    def test_eaten_checker_must_enter_first(self):
        board = self.game.init_board()
        board[0] = [1, 1]
        board[1] = [1, 1]
        moves = self.game.possible_moves(board, 1, [3, 5])
        self.assertTrue(all(position == 0 for position, _ in moves))

    def test_empty_bar_is_not_a_source(self):
        board = self.game.init_board()
        self.assertFalse(self.game.check_move(board, 1, 0, 3))

    def test_hit_sends_checker_to_bar(self):
        board = empty_board()
        board[1] = [2, 1]
        board[4] = [1, -1]
        board[20] = [2, -1]
        self.set_state(board, 1, [3, 6])
        self.assertTrue(self.game.make_move(1, 3))
        self.assertEqual(board[4], [1, 1])
        self.assertEqual(board[25], [1, -1])
        self.assertIn(('move', [(4, 25), (1, 4)]), self.controller.events)

    def test_cannot_land_on_blocked_point(self):
        board = empty_board()
        board[1] = [2, 1]
        board[4] = [2, -1]
        self.assertFalse(self.game.check_move(board, 1, 1, 3))

    def test_bear_off_with_higher_die_only_from_highest_point(self):
        board = empty_board()
        board[19] = [1, 1]
        board[23] = [1, 1]
        # 23 needs a 2 to bear off, a 5 can not be used while 19 is occupied
        self.assertFalse(self.game.check_move(board, 1, 23, 5))
        self.assertTrue(self.game.check_move(board, 1, 19, 5))
        self.assertTrue(self.game.check_move(board, 1, 19, 6))
        self.assertTrue(self.game.check_move(board, 1, 23, 2))

    def test_black_bear_off_with_higher_die(self):
        board = empty_board()
        board[6] = [1, -1]
        board[2] = [1, -1]
        self.assertFalse(self.game.check_move(board, -1, 2, 5))
        self.assertTrue(self.game.check_move(board, -1, 6, 6))
        self.assertTrue(self.game.check_move(board, -1, 2, 2))

    def test_no_bear_off_with_checker_outside_home(self):
        board = empty_board()
        board[18] = [1, 1]
        board[24] = [1, 1]
        self.assertFalse(self.game.check_move(board, 1, 24, 1))

    def test_must_use_both_dice_when_possible(self):
        board = empty_board()
        board[1] = [1, 1]
        board[24] = [2, -1]
        board[8] = [2, -1]
        moves = self.game.possible_moves(board, 1, [1, 6])
        # 1 -> 7 then 7 -> 8 is blocked, 1 -> 2 then 2 -> 8 is blocked, so only one die is usable
        # and it must be the higher one
        self.assertEqual(moves, [(1, 6)])

    def test_must_play_move_allowing_second_die(self):
        board = empty_board()
        board[1] = [1, 1]
        board[24] = [2, -1]
        board[7] = [2, -1]
        # 1 -> 7 is blocked, 1 -> 2 then 2 -> 8 uses both dice
        moves = self.game.possible_moves(board, 1, [1, 6])
        self.assertEqual(moves, [(1, 1)])

    def test_turn_passes_when_no_moves(self):
        board = empty_board()
        board[0] = [1, 1]
        for i in range(1, 7):
            board[i] = [2, -1]
        board[24] = [1, 1]
        self.game.board = board
        self.game.current_player = -1
        rolls = iter([[3, 4], [2, 5]])
        with mock.patch.object(self.game, 'roll_dice', side_effect=lambda: next(rolls)):
            self.game.new_turn()
        self.assertEqual(self.controller.events[0], ('no_moves', 1))
        self.assertEqual(self.game.current_player, -1)
        self.assertEqual(self.controller.events[-1], ('new_turn', -1))

    def test_turn_ends_after_dice_used(self):
        board = self.game.init_board()
        self.set_state(board, 1, [3, 5])
        with mock.patch.object(self.game, 'roll_dice', return_value=[1, 2]):
            self.assertTrue(self.game.make_move(1, 3))
            self.assertEqual(self.game.current_player, 1)
            self.assertTrue(self.game.make_move(4, 5))
        self.assertEqual(self.game.current_player, -1)
        self.assertEqual(self.controller.events[-1], ('new_turn', -1))

    def test_invalid_move_rejected(self):
        board = self.game.init_board()
        self.set_state(board, 1, [3, 5])
        self.assertFalse(self.game.make_move(1, 4))
        self.assertFalse(self.game.make_move(6, 3))

    def test_black_can_win(self):
        board = empty_board()
        board[2] = [1, -1]
        board[20] = [3, 1]
        self.set_state(board, -1, [2, 1])
        self.assertTrue(self.game.make_move(2, 2))
        self.assertEqual(self.controller.events[-2:], [('throw', 2), ('winner', -1)])

    def test_white_can_win(self):
        board = empty_board()
        board[24] = [1, 1]
        board[5] = [3, -1]
        self.set_state(board, 1, [6, 3])
        self.assertTrue(self.game.make_move(24, 6))
        self.assertEqual(self.controller.events[-2:], [('throw', 24), ('winner', 1)])


if __name__ == '__main__':
    unittest.main()
