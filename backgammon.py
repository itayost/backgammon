import random
import rules
from abstract_classes import abs_model


class backgammon(abs_model):

    def __init__(self):
        self.list_of_controllers = []
        self.board = []
        self.current_player = 0
        self.dice = []
        self.moves = []

        self.new_game()

    def new_game(self):
        self.board = rules.init_board()
        self.current_player = random.choice([-1, 1])
        self.send_new_game(self.board)
        self.new_turn()

    def new_turn(self):
        # A player without a legal move loses the turn, so keep passing until someone can move
        while True:
            self.current_player *= -1
            self.dice = self.roll_dice()
            self.moves = rules.possible_moves(self.board, self.current_player, self.dice)
            if len(self.moves) > 0:
                break
            self.send_no_moves()
        self.send_new_turn()

    def roll_dice(self):
        return rules.roll_dice()

    def make_move(self, position, jump):
        if (position, jump) not in self.moves:
            return False

        player = self.current_player
        moves_made, thrown = rules.apply_move(self.board, player, position, jump)
        self.dice.remove(jump)

        if thrown:
            if rules.checkers_left(self.board, player) == 0:
                self.moves = []
                self.send_throw(position)
                self.send_winner()
                return True
            self.moves = rules.possible_moves(self.board, player, self.dice)
            self.send_throw(position)
        else:
            self.moves = rules.possible_moves(self.board, player, self.dice)
            self.send_move(moves_made, self.moves)

        if len(self.moves) == 0:
            self.new_turn()
        return True

    def add_controller(self, listener):
        self.list_of_controllers.append(listener)
        listener.to_gui_new_game(self.board)
        listener.to_gui_new_turn(self.current_player, self.dice, self.moves)

    def send_new_game(self, board):
        for controller in self.list_of_controllers:
            controller.to_gui_new_game(board)

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

    def send_no_moves(self):
        for controller in self.list_of_controllers:
            controller.to_gui_no_moves(self.current_player, self.dice)

    def get_new_game(self):
        self.new_game()

    def get_move(self, start, jump):
        return self.make_move(start, jump)
