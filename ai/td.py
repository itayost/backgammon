"""A TD-Gammon style network: the board encoding of Tesauro, one hidden layer and the probability that white wins."""
import os

import numpy as np

import rules

WEIGHTS = os.path.join(os.path.dirname(__file__), 'weights', 'td.npz')
INPUTS = 198


def encode(board, player_to_move):
    x = np.zeros(INPUTS)
    i = 0
    for side in (1, -1):
        for point in range(1, 25):
            n = board[point][0] if board[point][1] == side else 0
            x[i] = n >= 1
            x[i + 1] = n >= 2
            x[i + 2] = n >= 3
            x[i + 3] = max(n - 3, 0) / 2
            i += 4
    x[192] = board[rules.WHITE_BAR][0] / 2
    x[193] = board[rules.BLACK_BAR][0] / 2
    x[194] = rules.borne_off(board, 1) / rules.CHECKERS_PER_PLAYER
    x[195] = rules.borne_off(board, -1) / rules.CHECKERS_PER_PLAYER
    x[196] = player_to_move == 1
    x[197] = player_to_move == -1
    return x


def sigmoid(z):
    return 1 / (1 + np.exp(-z))


class TDNet:
    def __init__(self, hidden=40, seed=0):
        rng = np.random.default_rng(seed)
        self.params = [
            rng.normal(0, 0.1, (hidden, INPUTS)),  # w1
            np.zeros(hidden),                      # b1
            rng.normal(0, 0.1, hidden),            # w2
            np.zeros(1),                           # b2
        ]

    def evaluate(self, X):
        w1, b1, w2, b2 = self.params
        return sigmoid(sigmoid(X @ w1.T + b1) @ w2 + b2)

    def value_and_grad(self, x):
        w1, b1, w2, b2 = self.params
        h = sigmoid(w1 @ x + b1)
        v = sigmoid(w2 @ h + b2)[0]
        dv = v * (1 - v)
        dh = dv * w2 * h * (1 - h)
        return v, [np.outer(dh, x), dh, dv * h, np.array([dv])]

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.savez(path, *self.params)

    @classmethod
    def load(cls, path):
        data = np.load(path)
        net = cls(hidden=data['arr_1'].shape[0])
        net.params = [data[f'arr_{i}'] for i in range(4)]
        return net


class TDEvaluator:
    def __init__(self, net):
        self.net = net

    @classmethod
    def load(cls, path=WEIGHTS):
        return cls(TDNet.load(path)) if os.path.exists(path) else None

    def evaluate(self, boards, player_to_move):
        X = np.array([encode(board, player_to_move) for board in boards])
        return self.net.evaluate(X).tolist()
