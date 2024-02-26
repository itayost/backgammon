import random
from abstract_classes import abs_model
from controller import *


class backgammon(abs_model):

    def __init__(self):
        self.list_of_controllers = []
        self.board = []
        self.current_player = 0
        self.dice = []
        self.moves = []
        self.p1_throwd = 15
        self.p2_throwd = 15

        self.new_game()

    def init_board(self):
        return [
            [0, 1], [2, 1], [0, 0], [0, 0], [0, 0], [0, 0], [5, -1], [0, 0], [3, -1],
            [0, 0], [0, 0], [0, 0], [5, 1], [5, -1], [0, 0], [0, 0], [0, 0], [3, 1],
            [0, 0], [5, 1], [0, 0], [0, 0], [0, 0], [0, 0], [2, -1], [0, -1],
        ]

    def init_board2(self):
        return [
            [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [4, -1], [2, -1], [3, -1], [0, 0],
            [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0],
            [0, 0], [1, -1], [1, -1], [1, -1], [0, 0], [0, 0], [1, 1], [0, 0],
        ]

    def new_game(self):
        self.board = self.init_board()
        self.current_player = random.choice([-1, 1])
        self.p1_throwd = 15
        self.p2_throwd = 15
        self.send_new_game(self.board)
        self.new_turn()

    def print_board(self):
        med = int(len(self.board) / 2)
        for i in range(med - 1, 0, -1):
            space = ''
            if self.board[i][1] != -1:
                space = ' '
            print(f'{space}{self.board[i][0] * self.board[i][1]} |', end='')
        print(f'p1 eatens = {self.board[0][0]}')
        for i in range(med, len(self.board) - 1):
            space = ''
            if self.board[i][1] != -1:
                space = ' '
            print(f'{space}{self.board[i][0] * self.board[i][1]} |', end='')
        print(f'p2 eatens = {self.board[len(self.board) - 1][0]}')

    def new_turn(self):
        self.current_player *= -1
        self.dice = self.roll_dice()
        self.moves = self.possible_moves(self.dice)
        self.send_new_turn()

    def update_moves_list(self, jump):
        if jump in self.dice:
            self.dice.remove(jump)
            if len(self.dice) == 0:
                self.new_turn()
                return
            self.moves = self.possible_moves(self.dice)
            if len(self.moves) == 0:
                self.new_turn()

    def roll_dice(self):
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        if die1 == die2:
            return [die1, die1, die1, die1]
        return [die1, die2]

    def make_move(self, position, jump):
        moves_made = []
        fixed_jump = jump * self.current_player
        if not self.check_move(position, jump):
            return False
        else:
            self.board[position][0] -= 1
            if self.board[position][0] == 0:
                self.board[position][1] = 0
            if 1 > position + fixed_jump or position + fixed_jump >= len(self.board) - 1:
                return self.make_throw(position, jump)
            elif self.board[position + fixed_jump][1] != self.current_player:
                if self.board[position + fixed_jump][1] == 0:
                    self.board[position + fixed_jump][1] = self.current_player
                    self.board[position + fixed_jump][0] += 1
                else:
                    eaten_dest = self.eaten(self.current_player * (- 1))
                    moves_made.append((position + fixed_jump, eaten_dest))
                    self.board[position + fixed_jump][1] = self.current_player
            else:
                self.board[position + fixed_jump][0] += 1
            moves_made.append((position, position + fixed_jump))
        self.update_moves_list(jump)
        self.send_move(moves_made, self.moves)
        print(f'eaten white: {self.board[0]}. eaten black: {self.board[25]}')
        return True

    def check_move(self, position, jump):
        # Check if jump is in dice
        if jump not in self.dice:
            return False

        # Check if player has eaten pieces and chose the position to take them out
        if self.has_eaten():
            if self.current_player == 1 and position != 0:
                return False
            elif self.current_player == -1 and position != len(self.board) - 1:
                return False

        # Check if the move is within bounds
        if position < 0 or position >= len(self.board):
            return False

        # Check if there are checkers on the starting point
        if self.board[position][1] != self.current_player:
            return False

        # Check if the destination is within bounds
        destination = position + (jump * self.current_player)
        if destination < 1 or destination >= len(self.board) - 1:
            if self.can_start_throwing(self.current_player):
                return True
            return False

        # Check if the destination is empty or has only one opposing checker
        if self.board[destination][0] <= 1 or self.board[destination][1] == self.current_player:
            return True
        return False

    def can_start_throwing(self, player):
        start_index = 1 if player == 1 else 7
        end_index = 19 if player == 1 else 25

        for i in range(start_index, end_index):
            if self.board[i][1] == player:
                return False

        return True

    def make_throw(self, position, jump):
        if self.current_player == 1:
            self.p1_throwd -= 1
            if self.p1_throwd == 0:
                self.send_winner()
                return
        else:
            self.p2_throwd -= 1
            if self.p1_throwd == 0:
                self.send_winner()
                return
        self.update_moves_list(jump)
        self.send_throw(position)

    def possible_throws(self, dice):
        all_moves = []
        start_index = 19 if self.current_player == 1 else 1
        end_index = 25 if self.current_player == 1 else 7
        for i in range(start_index, end_index):
            if self.board[i][1] == self.current_player:
                for jump in set(dice):
                    if self.check_move(i, jump):
                        all_moves.append((i, jump))
        return all_moves

    def has_eaten(self):
        if self.current_player == -1 and self.board[len(self.board) - 1][0] > 0:
            return True
        elif self.current_player == 1 and self.board[0][0] > 0:
            return True
        return False

    def eaten(self, eaten_player):
        if eaten_player == -1:
            self.board[len(self.board) - 1][0] += 1
            self.board[len(self.board) - 1][1] = -1
            return len(self.board) - 1
        else:
            self.board[0][0] += 1
            self.board[0][1] = 1
            return 0

    def eaten_moves(self, dice):
        all_moves = []
        position = 0
        if self.current_player == -1:
            position = len(self.board) - 1
        for jump in set(dice):
            if self.check_move(position, jump):
                all_moves.append((position, jump))
        return all_moves

    def possible_moves(self, dice):
        if self.has_eaten():
            return self.eaten_moves(dice)

        elif self.can_start_throwing(self.current_player):
            return self.possible_throws(dice)

        else:
            all_moves = []
            for i in range(1, len(self.board) - 1):
                if self.current_player == self.board[i][1]:
                    for jump in set(dice):
                        if self.check_move(i, jump):
                            all_moves.append((i, jump))
            return all_moves

    def add_controller(self, listener: controller):
        self.list_of_controllers.append(listener)
        listener.to_gui_new_game(self.board)
        listener.to_gui_new_turn(self.current_player, self.dice, self.moves)

    def send_new_game(self, board):
        for controller in self.list_of_controllers:
            controller.to_gui_new_game(board)
            self.send_new_turn()

    def send_move(self, moves_made, moves_available):
        for controller in self.list_of_controllers:
            controller.to_gui_new_move(moves_made, moves_available, self.dice)

    def send_throw(self, position):
        for controller in self.list_of_controllers:
            controller.to_gui_throw_made(position, self.moves, self.dice)

    def send_winner(self):
        for controller in self.list_of_controllers:
            controller.to_gui_winner(self.current_player)

    def send_new_turn(self):
        for controller in self.list_of_controllers:
            controller.to_gui_new_turn(self.current_player, self.dice, self.moves)

    def get_new_game(self):
        self.new_game()

    def get_move(self, start, jump):
        self.make_move(start, jump)
