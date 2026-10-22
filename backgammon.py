import random
from abstract_classes import abs_model

# Board layout: index 0 is the bar of player 1 (white), index 25 is the bar of
# player -1 (black), indices 1-24 are the points. Every cell is [count, owner].
# Player 1 moves from low to high indices and bears off past 24,
# player -1 moves from high to low indices and bears off below 1.
WHITE_BAR = 0
BLACK_BAR = 25
CHECKERS_PER_PLAYER = 15


class backgammon(abs_model):

    def __init__(self):
        self.list_of_controllers = []
        self.board = []
        self.current_player = 0
        self.dice = []
        self.moves = []

        self.new_game()

    def init_board(self):
        return [
            [0, 1], [2, 1], [0, 0], [0, 0], [0, 0], [0, 0], [5, -1], [0, 0], [3, -1],
            [0, 0], [0, 0], [0, 0], [5, 1], [5, -1], [0, 0], [0, 0], [0, 0], [3, 1],
            [0, 0], [5, 1], [0, 0], [0, 0], [0, 0], [0, 0], [2, -1], [0, -1],
        ]

    def new_game(self):
        self.board = self.init_board()
        self.current_player = random.choice([-1, 1])
        self.send_new_game(self.board)
        self.new_turn()

    def new_turn(self):
        # A player without a legal move loses the turn, so keep passing until someone can move
        while True:
            self.current_player *= -1
            self.dice = self.roll_dice()
            self.moves = self.possible_moves(self.board, self.current_player, self.dice)
            if len(self.moves) > 0:
                break
            self.send_no_moves()
        self.send_new_turn()

    def roll_dice(self):
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        if die1 == die2:
            return [die1, die1, die1, die1]
        return [die1, die2]

    def make_move(self, position, jump):
        if (position, jump) not in self.moves:
            return False

        player = self.current_player
        moves_made, thrown = self.apply_move(self.board, player, position, jump)
        self.dice.remove(jump)

        if thrown:
            if self.checkers_left(player) == 0:
                self.moves = []
                self.send_throw(position)
                self.send_winner()
                return True
            self.moves = self.possible_moves(self.board, player, self.dice)
            self.send_throw(position)
        else:
            self.moves = self.possible_moves(self.board, player, self.dice)
            self.send_move(moves_made, self.moves)

        if len(self.moves) == 0:
            self.new_turn()
        return True

    @staticmethod
    def bar_of(player):
        return WHITE_BAR if player == 1 else BLACK_BAR

    @staticmethod
    def owns(board, position, player):
        return board[position][0] > 0 and board[position][1] == player

    def has_eaten(self, board, player):
        return board[self.bar_of(player)][0] > 0

    def can_start_throwing(self, board, player):
        home = range(19, 25) if player == 1 else range(1, 7)
        for i in range(len(board)):
            if i not in home and self.owns(board, i, player):
                return False
        return True

    def check_move(self, board, player, position, jump):
        # Check if the move is within bounds and there are checkers of the player on the starting point
        if position < 0 or position >= len(board) or not self.owns(board, position, player):
            return False

        # Check if player has eaten pieces and chose the position to take them out
        if self.has_eaten(board, player) and position != self.bar_of(player):
            return False

        destination = position + (jump * player)
        if 1 <= destination <= 24:
            # The destination must be empty, hold only one opposing checker or belong to the player
            return board[destination][0] <= 1 or board[destination][1] == player

        # Throwing a checker off the board
        if not self.can_start_throwing(board, player):
            return False
        distance = 25 - position if player == 1 else position
        if jump == distance:
            return True
        # A higher die may be used only when no checker sits farther from home
        farther = range(19, position) if player == 1 else range(position + 1, 7)
        for i in farther:
            if self.owns(board, i, player):
                return False
        return True

    def apply_move(self, board, player, position, jump):
        """Applies a valid move on the board, returns the moves made for the gui and whether a checker was thrown"""
        moves_made = []
        board[position][0] -= 1
        if board[position][0] == 0 and position != self.bar_of(player):
            board[position][1] = 0

        destination = position + (jump * player)
        if destination < 1 or destination > 24:
            return moves_made, True

        if board[destination][1] == -player and board[destination][0] == 1:
            eaten_dest = self.bar_of(-player)
            board[eaten_dest][0] += 1
            board[eaten_dest][1] = -player
            moves_made.append((destination, eaten_dest))
            board[destination][0] = 0
        board[destination][0] += 1
        board[destination][1] = player
        moves_made.append((position, destination))
        return moves_made, False

    def single_moves(self, board, player, dice):
        all_moves = []
        for i in range(len(board)):
            if self.owns(board, i, player):
                for jump in sorted(set(dice)):
                    if self.check_move(board, player, i, jump):
                        all_moves.append((i, jump))
        return all_moves

    def max_dice_used(self, board, player, dice):
        """The maximal number of dice the player can use from this board"""
        if len(dice) == 0:
            return 0
        # Throwing off the last checker ends the game, the remaining dice are not needed
        if not any(cell[0] > 0 and cell[1] == player for cell in board):
            return len(dice)
        best = 0
        for position, jump in self.single_moves(board, player, dice):
            next_board = [cell[:] for cell in board]
            self.apply_move(next_board, player, position, jump)
            next_dice = list(dice)
            next_dice.remove(jump)
            best = max(best, 1 + self.max_dice_used(next_board, player, next_dice))
            if best == len(dice):
                break
        return best

    def possible_moves(self, board, player, dice):
        """Legal moves according to the rules: as many dice as possible must be used,
        and when only one of two different dice can be used it must be the higher one"""
        moves = self.single_moves(board, player, dice)
        if len(dice) < 2 or len(moves) == 0:
            return moves

        used = {}
        for position, jump in moves:
            next_board = [cell[:] for cell in board]
            self.apply_move(next_board, player, position, jump)
            next_dice = list(dice)
            next_dice.remove(jump)
            used[(position, jump)] = 1 + self.max_dice_used(next_board, player, next_dice)

        best = max(used.values())
        moves = [move for move in moves if used[move] == best]
        if best == 1 and len(set(dice)) == 2:
            higher = [move for move in moves if move[1] == max(dice)]
            if len(higher) > 0:
                moves = higher
        return moves

    def checkers_left(self, player):
        return sum(cell[0] for cell in self.board if cell[1] == player)

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
        self.make_move(start, jump)
