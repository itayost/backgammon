from abstract_classes import *


class controller:
    def __init__(self, model: abs_model, gui: abs_gui):
        self.model = model
        self.gui = gui
        self.gui.add_controller(self)
        self.model.add_controller(self)

    def to_gui_new_move(self, moves_made, moves_available, dice):
        self.gui.get_move(moves_made, moves_available, dice)

    def to_gui_throw_made(self, position, moves_available, dice):
        self.gui.get_throw(position, moves_available, dice)

    def to_gui_new_game(self, board):
        self.gui.get_new_game(board)

    def to_gui_new_turn(self, player, dice, moves):
        self.gui.get_new_turn(player, dice, moves)

    def to_gui_winner(self, player):
        self.gui.get_winner(player)

    def to_model_try_move(self, start, jump):
        self.model.get_move(start, jump)

    def to_model_new_game(self):
        self.model.get_new_game()
