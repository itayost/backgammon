"""One game of backgammon as a turn state machine, without any gui.

The players roll, move one die at a time, may undo moves inside their turn, and end the turn
with end_turn(). Listeners get every change as (event, data) and read the state from the session.
"""
import random
from dataclasses import dataclass, field
from enum import Enum

import rules


class Phase(Enum):
    AWAIT_ROLL = 'await_roll'
    MOVING = 'moving'
    READY_TO_END = 'ready_to_end'
    GAME_OVER = 'game_over'


NO_LEGAL_MOVES = 'no legal moves'


@dataclass
class GameStats:
    turns: int = 0
    hits: dict = field(default_factory=lambda: {1: 0, -1: 0})
    winner: int = None
    resigned: bool = False


class GameSession:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.listeners = []
        self.board = rules.init_board()
        self.player = 1
        self.phase = Phase.GAME_OVER
        self.dice = []
        self.dice_left = []
        self.legal = []
        self.reason = None
        self.opening = None
        self.history = []
        self.stats = GameStats()

    def add_listener(self, listener):
        self.listeners.append(listener)

    def remove_listener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    def emit(self, event, **data):
        for listener in list(self.listeners):
            listener(event, data)

    # Game flow

    def start(self, opening=None):
        """Starts a new game with the opening roll: each side rolls one die, ties roll again,
        and the higher die moves first using both dice. opening=(white die, black die) fixes it."""
        self.board = rules.init_board()
        self.stats = GameStats()
        if opening is None:
            white, black = self.die(), self.die()
            while white == black:
                white, black = self.die(), self.die()
        else:
            white, black = opening
        self.opening = (white, black)
        self.player = 1 if white > black else -1
        self.phase = Phase.AWAIT_ROLL
        self.dice, self.dice_left, self.legal, self.history, self.reason = [], [], [], [], None
        self.emit('game_started')
        self.begin_moves([white, black])

    def roll(self, dice=None):
        if self.phase != Phase.AWAIT_ROLL:
            return False
        dice = list(dice) if dice is not None else rules.roll_dice_with(self.rng)
        self.opening = None
        self.emit('rolled', player=self.player, dice=list(dice))
        self.begin_moves(dice)
        return True

    def begin_moves(self, dice):
        self.dice = list(dice)
        self.dice_left = list(dice)
        self.history = []
        self.refresh_legal()
        self.emit('turn_changed')

    def move(self, position, jump):
        """Plays one die, returns False when the move is not legal now"""
        if self.phase != Phase.MOVING or (position, jump) not in self.legal:
            return False
        self.history.append((rules.copy_board(self.board), list(self.dice_left), dict(self.stats.hits)))
        moves_made, thrown = rules.apply_move(self.board, self.player, position, jump)
        self.dice_left.remove(jump)
        hit = len(moves_made) == 2
        if hit:
            self.stats.hits[self.player] += 1
        destination = None if thrown else moves_made[-1][1]
        self.emit('stepped', player=self.player, start=position, end=destination, hit=hit)
        if thrown and rules.checkers_left(self.board, self.player) == 0:
            self.finish(self.player)
            return True
        self.refresh_legal()
        self.emit('turn_changed')
        return True

    def undo(self):
        if self.phase not in (Phase.MOVING, Phase.READY_TO_END) or not self.history:
            return False
        self.board, self.dice_left, self.stats.hits = self.history.pop()
        self.refresh_legal()
        self.emit('undone')
        self.emit('turn_changed')
        return True

    def end_turn(self):
        if self.phase != Phase.READY_TO_END:
            return False
        self.stats.turns += 1
        self.player = -self.player
        self.phase = Phase.AWAIT_ROLL
        self.dice = []
        self.dice_left = []
        self.legal = []
        self.reason = None
        self.history = []
        self.opening = None
        self.emit('turn_started', player=self.player)
        return True

    def resign(self, player):
        if self.phase == Phase.GAME_OVER:
            return False
        self.stats.resigned = True
        self.finish(-player)
        return True

    def finish(self, winner):
        self.stats.winner = winner
        self.phase = Phase.GAME_OVER
        self.legal = []
        self.emit('game_over', winner=winner)

    # Helpers

    def die(self):
        return self.rng.randint(1, 6)

    def refresh_legal(self):
        self.legal = rules.possible_moves(self.board, self.player, self.dice_left) if self.dice_left else []
        if self.legal:
            self.phase = Phase.MOVING
            self.reason = None
        else:
            self.phase = Phase.READY_TO_END
            # Nothing was played this turn although dice were rolled: say why the turn passes
            self.reason = NO_LEGAL_MOVES if not self.history else None

    def can_undo(self):
        return bool(self.history) and self.phase in (Phase.MOVING, Phase.READY_TO_END)

    def pips(self, player):
        total = 0
        for index, (count, owner) in enumerate(self.board):
            if count and owner == player:
                distance = 25 if index == rules.bar_of(player) else (25 - index if player == 1 else index)
                total += count * distance
        return total

    def destination(self, position, jump):
        """Where a move lands, None when it bears the checker off"""
        end = position + jump * self.player
        return end if 1 <= end <= 24 else None
