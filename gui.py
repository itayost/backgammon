from col_container import TriangleItem, PointItem, throwing_rectangle, communication, Colable
from abstract_classes import abs_gui
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsRectItem, QDialog
from PyQt6.QtGui import QColor
from enum import Enum

from winner_dialog import WinnerDialog


class Color(Enum):
    White = 1
    Black = -1


class BackgammonBoard(QGraphicsView, abs_gui):
    def __init__(self):
        super().__init__()
        self.list_of_controllers = []
        self.dice_text = None
        self.current_player_text = None
        self.message_text = None
        self.messages = []
        self.throw_area = None
        self.current_player = 0
        self.dice = None
        self.computer_players = set()
        # Called instead of closing when the players do not want another game
        self.on_quit = None

        self.point_radius = 25
        self.point_spacing = 61
        self.board_width = 940
        self.board_height = 600
        self.triangle_height = 250
        self.triangle_width = 50

        self.moves = []
        self.selected_piece = None
        self.selected_col = None
        self.board_of_points = []
        self.board_of_cols = []

        self.setWindowTitle("Backgammon")
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.init_board()

    def init_board(self):
        # Draw the board background
        self.scene.addRect(0, 0, self.board_width, self.board_height)
        self.scene.setBackgroundBrush(QColor("burlywood"))

        self.current_player_text = QGraphicsTextItem("Current Player: ")
        self.current_player_text.setPos(self.board_width / 2 + self.point_spacing, self.board_height / 2 - 50)
        self.scene.addItem(self.current_player_text)

        self.dice_text = QGraphicsTextItem("Dice: ")
        self.dice_text.setPos(self.board_width / 2 + self.point_spacing, self.board_height / 2)
        self.scene.addItem(self.dice_text)

        self.message_text = QGraphicsTextItem("")
        self.message_text.setPos(self.point_spacing, self.board_height / 2 - 25)
        self.scene.addItem(self.message_text)

        self.init_triangles()
        self.init_mid()
        self.init_thrown_section()
        self.setSceneRect(0, 0, self.board_width, self.board_height)

    @staticmethod
    def color_name(player):
        return "White" if Color.White.value == player else "Black"

    def set_computer_players(self, players):
        self.computer_players = set(players)

    def update_info_display(self, current_player, dice):
        computer = " (computer)" if current_player in self.computer_players else ""
        self.current_player_text.setPlainText(f"Current Player: {self.color_name(current_player)}{computer}")
        self.dice_text.setPlainText(f"Dice: {dice}")

    def show_messages(self):
        self.message_text.setPlainText("\n".join(self.messages))

    def init_triangles(self):
        y_up = 0
        for i in range(0, 13):
            x_up = self.calc_x_of_col(i)
            color = "darkgoldenrod" if i % 2 == 0 else "red"

            triangle_up = TriangleItem(i, x_up + self.point_radius, y_up, self.triangle_height, self.triangle_width,
                                       color, "down")
            triangle_up.clicked.communicate.connect(self.select_piece)
            self.board_of_cols.append(triangle_up)
            self.scene.addItem(triangle_up)

        y_down = self.board_height
        for i in range(13, 26):
            x_down = self.calc_x_of_col(i)
            color = "darkgoldenrod" if i % 2 == 0 else "red"

            triangle_down = TriangleItem(i, x_down + self.point_radius, y_down, self.triangle_height,
                                         self.triangle_width, color, "up")
            triangle_down.clicked.communicate.connect(self.select_piece)
            self.board_of_cols.append(triangle_down)
            self.scene.addItem(triangle_down)

    def init_mid(self):
        rect1 = QGraphicsRectItem(self.calc_x_of_col(0), 0, self.triangle_width, self.board_height)
        rect1.setBrush(QColor("brown"))
        rect1.setEnabled(False)
        self.scene.addItem(rect1)

    def init_thrown_section(self):
        self.throw_area = throwing_rectangle(-1, self.calc_x_of_col(1) + self.point_spacing, 0, self.point_spacing,
                                            self.board_height)
        self.throw_area.clicked.communicate.connect(self.select_throw)
        self.scene.addItem(self.throw_area)

    def print_col(self, col):
        count = len(self.board_of_points[col])
        if count == 0:
            return
        x = self.calc_x_of_col(col)
        y = self.calc_y_of_col(col)
        direction = "down" if col <= 12 else "up"
        fixed_triange = (self.triangle_height / 2) - 10 if col == 0 or col == 25 else self.triangle_height
        space = self.point_radius * 2 if count * (self.point_radius * 2) < fixed_triange else fixed_triange / count
        for i in range(count):
            self.board_of_points[col][i].setPos(x, y)
            if direction == "down":
                y += space
            else:
                y -= space

    def add_piece(self, player, col):
        checker = PointItem(0, 0, self.point_radius, player, col)
        checker.clicked.communicate.connect(self.select_piece)
        self.scene.addItem(checker)
        return checker

    def init_pieces_board(self, board):
        self.board_of_points = [[] for l in range(len(board))]
        for i in range(0, 26):
            player = board[i][1]
            count = board[i][0]
            if player != 0:
                for j in range(count):
                    checker = self.add_piece(player, i)
                    self.board_of_points[i].append(checker)
                self.print_col(i)

    def clear_board(self):
        for col in self.board_of_points:
            for i in range(0, len(col)):
                temp = col.pop()
                self.scene.removeItem(temp)

    def move_piece(self, start, dest):
        temp = self.board_of_points[start].pop()
        self.board_of_points[dest].append(temp)
        temp.col = dest
        self.print_col(start)
        self.print_col(dest)

    def select_piece(self):
        if self.sender() is not None and isinstance(self.sender(), communication):
            if self.sender().point_item is not None and isinstance(self.sender().point_item, Colable):
                if self.selected_piece is not None:
                    if self.selected_piece == self.sender().point_item.col:
                        self.selected_piece = None
                    else:
                        start = self.selected_piece
                        jump = abs(self.sender().point_item.col - start)
                        self.selected_piece = None
                        self.selected_col = None
                        self.send_move(start, jump)
                else:
                    self.selected_piece = self.sender().point_item.col
                self.enable_choosing_cols(self.selected_piece)

    def select_throw(self):
        if self.sender() is not None and isinstance(self.sender(), communication):
            if isinstance(self.sender().point_item, throwing_rectangle) and self.selected_piece is not None:
                jump = self.find_die()
                start = self.selected_piece
                self.selected_piece = None
                self.selected_col = None
                if jump is not None:
                    self.send_move(start, jump)
                self.enable_choosing_cols(self.selected_piece)

    def setEnabled_col(self, col, flag):
        self.board_of_cols[col].setEnabled(flag)
        self.board_of_cols[col].is_marked(flag)
        for piece in self.board_of_points[col]:
            piece.setEnabled(flag)
            piece.is_marked(flag)

    def is_throw_move(self, move):
        destination = move[0] + (move[1] * self.current_player)
        return destination < 1 or destination > 24

    def enable_choosing_cols(self, col=None):
        if self.current_player in self.computer_players:
            # Clicks are locked while the computer plays
            list_of_cols = []
            can_throw = False
            col = None
        elif col is None:
            list_of_cols = [move[0] for move in self.moves]
            can_throw = False
        else:
            list_of_cols = [move[0] + (move[1] * self.current_player) for move in self.moves
                            if move[0] == col and not self.is_throw_move(move)]
            can_throw = any(move[0] == col and self.is_throw_move(move) for move in self.moves)
        for i in range(0, len(self.board_of_points)):
            flag_piece = i in list_of_cols or i == col
            self.setEnabled_col(i, flag_piece)
        self.throw_area.setEnabled(can_throw)
        self.throw_area.is_marked(can_throw)

    def calc_x_of_col(self, col):
        if col == 0 or col == 25:
            return (6 * self.point_spacing) + self.point_spacing
        x = ((13 - col) * self.point_spacing) if col <= 12 else ((col - 12) * self.point_spacing)
        if 1 <= col <= 6 or 19 <= col <= 24:
            x += self.point_spacing
        return x

    def calc_y_of_col(self, col):
        if col == 0:
            return (self.point_radius * 2) * 3
        elif col == 25:
            return self.board_height - (self.point_radius * 2) - (self.point_radius * 2) * 3
        elif 1 <= col <= 12:
            return 0
        else:
            return self.board_height - (self.point_radius * 2)

    def find_die(self):
        # The smallest die that throws the selected checker off the board
        return min((move[1] for move in self.moves if move[0] == self.selected_piece and self.is_throw_move(move)),
                   default=None)

    def add_controller(self, listener):
        self.list_of_controllers.append(listener)

    def get_new_game(self, board):
        self.selected_piece = None
        self.selected_col = None
        self.messages = []
        self.show_messages()
        self.clear_board()
        self.init_pieces_board(board)

    def get_move(self, moves_made, moves_available, dice):
        for move in moves_made:
            self.move_piece(move[0], move[1])
        self.after_move(moves_available, dice)

    def get_throw(self, position, moves_available, dice):
        temp = self.board_of_points[position].pop()
        self.scene.removeItem(temp)
        self.print_col(position)
        self.after_move(moves_available, dice)

    def after_move(self, moves_available, dice):
        self.moves = moves_available
        self.dice = dice
        self.messages = []
        self.show_messages()
        self.update_info_display(self.current_player, self.dice)
        self.enable_choosing_cols(self.selected_piece)

    def get_winner(self, player):
        winner_dialog = WinnerDialog(self.color_name(player), self)
        result = winner_dialog.exec()

        if result == QDialog.DialogCode.Accepted.value:
            self.send_new_game()
        elif self.on_quit is not None:
            self.on_quit()
        else:
            self.close()

    def get_new_turn(self, player, dice, moves):
        self.current_player = player
        self.selected_piece = None
        self.selected_col = None
        self.update_info_display(player, dice)
        self.dice = dice
        self.moves = moves
        self.enable_choosing_cols()

    def get_no_moves(self, player, dice):
        self.messages.append(f"{self.color_name(player)} rolled {dice} and has no moves")
        self.show_messages()

    def send_new_game(self):
        for controller in self.list_of_controllers:
            controller.to_model_new_game()

    def send_move(self, col, jump):
        for controller in self.list_of_controllers:
            controller.to_model_try_move(col, jump)
