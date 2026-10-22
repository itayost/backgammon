import rules


def board_key(board):
    # An empty cell may keep its last owner, so it is ignored to compare positions correctly
    return tuple((count, owner if count else 0) for count, owner in board)


def full_moves(board, player, dice):
    """All the distinct positions the player can reach with the dice, as a list of (board, steps).
    The steps are (position, jump) pairs in the order the model accepts them.
    When there is no legal move the result holds the board as it is with no steps."""
    results = {}

    def expand(current, remaining, steps):
        moves = rules.possible_moves(current, player, remaining)
        if not moves:
            results.setdefault(board_key(current), (current, steps))
            return
        for position, jump in moves:
            next_board = rules.copy_board(current)
            rules.apply_move(next_board, player, position, jump)
            next_dice = list(remaining)
            next_dice.remove(jump)
            expand(next_board, next_dice, steps + [(position, jump)])

    expand(rules.copy_board(board), list(dice), [])
    return list(results.values())


def all_rolls():
    """The 21 distinct rolls with their probability"""
    rolls = []
    for die1 in range(1, 7):
        for die2 in range(die1, 7):
            if die1 == die2:
                rolls.append(([die1] * 4, 1 / 36))
            else:
                rolls.append(([die1, die2], 2 / 36))
    return rolls
