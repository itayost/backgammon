"""Trains the network by playing against itself with TD(lambda).

Usage: python -m ai.train_td [games] [--resume]
Every 1000 games it saves the weights and reports the win rate against the hand written evaluation.
"""
import random
import sys
import time

import numpy as np

import rules
from ai.bench import play_game
from ai.evaluators import HeuristicEvaluator
from ai.player import ComputerPlayer
from ai.td import TDNet, TDEvaluator, WEIGHTS, encode


def train_game(net, evaluator, rng, alpha, lam):
    computer = ComputerPlayer('medium', evaluator=evaluator, rng=rng)
    board = rules.init_board()
    player = rng.choice([1, -1])
    v, grads = net.value_and_grad(encode(board, player))
    traces = [np.array(g) for g in grads]
    while True:
        dice = rules.roll_dice()
        for position, jump in computer.choose(board, player, dice):
            rules.apply_move(board, player, position, jump)

        if rules.checkers_left(board, player) == 0:
            delta = (1.0 if player == 1 else 0.0) - v
            for p, e in zip(net.params, traces):
                p += alpha * delta * e
            return

        player = -player
        v_next, grads = net.value_and_grad(encode(board, player))
        delta = v_next - v
        for p, e in zip(net.params, traces):
            p += alpha * delta * e
        traces = [lam * e + g for e, g in zip(traces, grads)]
        v = v_next


def win_rate_against_heuristic(evaluator, games, seed):
    rng = random.Random(seed)
    wins = 0
    for game in range(games):
        td_side = 1 if game % 2 == 0 else -1
        players = {td_side: ComputerPlayer('medium', evaluator=evaluator, rng=rng),
                   -td_side: ComputerPlayer('medium', evaluator=HeuristicEvaluator(), rng=rng)}
        wins += play_game(players, rng) == td_side
    return wins / games


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 10000
    net = TDNet.load(WEIGHTS) if '--resume' in sys.argv else TDNet()
    evaluator = TDEvaluator(net)
    rng = random.Random(0)
    start = time.time()
    for game in range(1, games + 1):
        alpha = 0.1 if game < games // 2 else 0.05
        train_game(net, evaluator, rng, alpha, lam=0.7)
        if game % 1000 == 0:
            net.save(WEIGHTS)
            rate = win_rate_against_heuristic(evaluator, 100, seed=game)
            print(f'{game} games, {time.time() - start:.0f}s, wins against the heuristic: {rate:.0%}', flush=True)
    net.save(WEIGHTS)


if __name__ == '__main__':
    main()
