from abc import ABC, abstractmethod


# abs_gui can not inherit ABC, its implementation is also a Qt widget and the two metaclasses conflict
class abs_gui:
    @abstractmethod
    def get_new_game(self, board):
        pass

    @abstractmethod
    def get_move(self, moves_made, moves_available, dice):
        pass

    @abstractmethod
    def get_throw(self, position, moves_available, dice):
        pass

    @abstractmethod
    def get_winner(self, player):
        pass

    @abstractmethod
    def get_new_turn(self, player, dice, moves):
        pass

    @abstractmethod
    def get_no_moves(self, player, dice):
        pass

    @abstractmethod
    def send_new_game(self):
        pass

    @abstractmethod
    def send_move(self, col, jump):
        pass

    @abstractmethod
    def add_controller(self, listener):
        pass


class abs_model(ABC):
    @abstractmethod
    def send_new_game(self, board):
        pass

    @abstractmethod
    def send_move(self, moves_made, moves_available):
        pass

    @abstractmethod
    def send_throw(self, position):
        pass

    @abstractmethod
    def send_winner(self):
        pass

    @abstractmethod
    def send_new_turn(self):
        pass

    @abstractmethod
    def send_no_moves(self):
        pass

    @abstractmethod
    def get_new_game(self):
        pass

    @abstractmethod
    def get_move(self, start, jump):
        pass

    @abstractmethod
    def add_controller(self, listener):
        pass
