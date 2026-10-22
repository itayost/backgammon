"""Plays games between two computer players without the gui.

Usage: python -m ai.bench [games] [white player] [black player] [seed]
players: random, easy, medium, hard, or td:<level> to use the trained network at that level
"""
import math
import random
import sys
import time

import rules
from ai.player import ComputerPlayer, RandomPlayer


def make_player(name, seed):
    """random, a level (easy, medium, hard), or td:<level> for a level that uses the trained network"""
    if name == 'random':
        return RandomPlayer(random.Random(seed))
    if name.startswith('td:'):
        from ai.td import TDEvaluator
        evaluator = TDEvaluator.load()
        if evaluator is None:
            raise SystemExit('no trained network, run python -m ai.train_td first')
        return ComputerPlayer(name[3:], evaluator=evaluator, rng=random.Random(seed))
    return ComputerPlayer(name, rng=random.Random(seed))


def play_game(players, rng):
    """Plays one game and returns the winner, players maps 1 and -1 to a player"""
    board = rules.init_board()
    player = rng.choice([1, -1])
    while True:
        dice = [rng.randint(1, 6), rng.randint(1, 6)]
        if dice[0] == dice[1]:
            dice = dice * 2
        for position, jump in players[player].choose(board, player, dice):
            assert (position, jump) in rules.possible_moves(board, player, dice), 'illegal move'
            rules.apply_move(board, player, position, jump)
            dice.remove(jump)
            if rules.checkers_left(board, player) == 0:
                return player
        assert not rules.possible_moves(board, player, dice), 'the move did not use all the dice it could'
        player = -player


def bench(games, white, black, seed=0):
    rng = random.Random(seed)
    players = {1: make_player(white, seed + 1), -1: make_player(black, seed + 2)}
    wins = 0
    start = time.time()
    for _ in range(games):
        wins += play_game(players, rng) == 1
    rate = wins / games
    error = 1.96 * math.sqrt(rate * (1 - rate) / games)
    return rate, error, time.time() - start


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    white_name = sys.argv[2] if len(sys.argv) > 2 else 'medium'
    black_name = sys.argv[3] if len(sys.argv) > 3 else 'random'
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    win_rate, margin, seconds = bench(n, white_name, black_name, seed)
    print(f'{white_name} (white) vs {black_name} (black): white won {win_rate:.0%} +- {margin:.0%} '
          f'of {n} games in {seconds:.0f}s')
