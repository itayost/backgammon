"""Backgammon rules as pure functions over a board, shared by the model and the computer player.

Board layout: index 0 is the bar of player 1 (white), index 25 is the bar of
player -1 (black), indices 1-24 are the points. Every cell is [count, owner].
Player 1 moves from low to high indices and bears off past 24,
player -1 moves from high to low indices and bears off below 1.
"""
import random

WHITE_BAR = 0
BLACK_BAR = 25
CHECKERS_PER_PLAYER = 15


def init_board():
    return [
        [0, 1], [2, 1], [0, 0], [0, 0], [0, 0], [0, 0], [5, -1], [0, 0], [3, -1],
        [0, 0], [0, 0], [0, 0], [5, 1], [5, -1], [0, 0], [0, 0], [0, 0], [3, 1],
        [0, 0], [5, 1], [0, 0], [0, 0], [0, 0], [0, 0], [2, -1], [0, -1],
    ]


def copy_board(board):
    return [cell[:] for cell in board]


def roll_dice():
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    if die1 == die2:
        return [die1, die1, die1, die1]
    return [die1, die2]


def bar_of(player):
    return WHITE_BAR if player == 1 else BLACK_BAR


def owns(board, position, player):
    return board[position][0] > 0 and board[position][1] == player


def has_eaten(board, player):
    return board[bar_of(player)][0] > 0


def checkers_left(board, player):
    return sum(cell[0] for cell in board if cell[1] == player)


def borne_off(board, player):
    return CHECKERS_PER_PLAYER - checkers_left(board, player)


def can_start_throwing(board, player):
    home = range(19, 25) if player == 1 else range(1, 7)
    for i in range(len(board)):
        if i not in home and owns(board, i, player):
            return False
    return True


def check_move(board, player, position, jump):
    # Check if the move is within bounds and there are checkers of the player on the starting point
    if position < 0 or position >= len(board) or not owns(board, position, player):
        return False

    # Check if player has eaten pieces and chose the position to take them out
    if has_eaten(board, player) and position != bar_of(player):
        return False

    destination = position + (jump * player)
    if 1 <= destination <= 24:
        # The destination must be empty, hold only one opposing checker or belong to the player
        return board[destination][0] <= 1 or board[destination][1] == player

    # Throwing a checker off the board
    if not can_start_throwing(board, player):
        return False
    distance = 25 - position if player == 1 else position
    if jump == distance:
        return True
    # A higher die may be used only when no checker sits farther from home
    farther = range(19, position) if player == 1 else range(position + 1, 7)
    for i in farther:
        if owns(board, i, player):
            return False
    return True


def apply_move(board, player, position, jump):
    """Applies a valid move on the board, returns the moves made for the gui and whether a checker was thrown"""
    moves_made = []
    board[position][0] -= 1
    if board[position][0] == 0 and position != bar_of(player):
        board[position][1] = 0

    destination = position + (jump * player)
    if destination < 1 or destination > 24:
        return moves_made, True

    if board[destination][1] == -player and board[destination][0] == 1:
        eaten_dest = bar_of(-player)
        board[eaten_dest][0] += 1
        board[eaten_dest][1] = -player
        moves_made.append((destination, eaten_dest))
        board[destination][0] = 0
    board[destination][0] += 1
    board[destination][1] = player
    moves_made.append((position, destination))
    return moves_made, False


def single_moves(board, player, dice):
    all_moves = []
    for i in range(len(board)):
        if owns(board, i, player):
            for jump in sorted(set(dice)):
                if check_move(board, player, i, jump):
                    all_moves.append((i, jump))
    return all_moves


def max_dice_used(board, player, dice):
    """The maximal number of dice the player can use from this board"""
    if len(dice) == 0:
        return 0
    # Throwing off the last checker ends the game, the remaining dice are not needed
    if checkers_left(board, player) == 0:
        return len(dice)
    best = 0
    for position, jump in single_moves(board, player, dice):
        next_board = copy_board(board)
        apply_move(next_board, player, position, jump)
        next_dice = list(dice)
        next_dice.remove(jump)
        best = max(best, 1 + max_dice_used(next_board, player, next_dice))
        if best == len(dice):
            break
    return best


def possible_moves(board, player, dice):
    """Legal moves according to the rules: as many dice as possible must be used,
    and when only one of two different dice can be used it must be the higher one"""
    moves = single_moves(board, player, dice)
    if len(dice) < 2 or len(moves) == 0:
        return moves

    used = {}
    for position, jump in moves:
        next_board = copy_board(board)
        apply_move(next_board, player, position, jump)
        next_dice = list(dice)
        next_dice.remove(jump)
        used[(position, jump)] = 1 + max_dice_used(next_board, player, next_dice)

    best = max(used.values())
    moves = [move for move in moves if used[move] == best]
    if best == 1 and len(set(dice)) == 2:
        higher = [move for move in moves if move[1] == max(dice)]
        if len(higher) > 0:
            moves = higher
    return moves
