import math
import rules

# Number of rolls out of 36 that hit a blot at a given distance from a single shooter (ignoring blocked points)
SHOTS = {1: 11, 2: 12, 3: 14, 4: 15, 5: 15, 6: 17, 7: 6, 8: 6, 9: 5, 10: 3, 11: 2, 12: 3,
         15: 1, 16: 1, 18: 1, 20: 1, 24: 1}


def sigmoid(z):
    return 1 / (1 + math.exp(-z))


def pip(index, player):
    """How far a checker is from bearing off"""
    if index == rules.bar_of(player):
        return 25
    return 25 - index if player == 1 else index


class HeuristicEvaluator:
    """Hand written evaluation, returns the probability that white wins"""

    def evaluate(self, boards, player_to_move):
        return [self.evaluate_one(board, player_to_move) for board in boards]

    def evaluate_one(self, board, player_to_move):
        white = self.features(board, 1, player_to_move)
        black = self.features(board, -1, player_to_move)

        if not self.has_contact(board):
            effective_white = white['pip'] + 2 * white['on_board']
            effective_black = black['pip'] + 2 * black['on_board']
            diff = effective_black - effective_white + (4 if player_to_move == 1 else -4)
            return sigmoid(2.5 * diff / math.sqrt((effective_white + effective_black) / 2 + 1))

        score = 0.03 * (black['pip'] - white['pip'])
        score += 0.2 * (white['home_points'] * (1 + 0.5 * black['bar']) -
                        black['home_points'] * (1 + 0.5 * white['bar']))
        score += 0.04 * (white['prime'] ** 2 - black['prime'] ** 2)
        score += 0.25 * (min(white['anchors'], 2) - min(black['anchors'], 2))
        score -= 0.05 * (white['risk'] - black['risk'])
        score -= 0.3 * (white['bar'] - black['bar'])
        score += 0.15 * (black['on_board'] - white['on_board'])
        return sigmoid(score)

    @staticmethod
    def has_contact(board):
        white = [i for i in range(26) if rules.owns(board, i, 1)]
        black = [i for i in range(26) if rules.owns(board, i, -1)]
        if not white or not black:
            return False
        return min(white) < max(black)

    def features(self, board, player, player_to_move):
        home = range(19, 25) if player == 1 else range(1, 7)
        opponent_home = range(1, 7) if player == 1 else range(19, 25)
        made = [1 <= i <= 24 and board[i][1] == player and board[i][0] >= 2 for i in range(26)]

        prime = run = 0
        for i in range(1, 25):
            run = run + 1 if made[i] else 0
            prime = max(prime, run)

        risk = 0.0
        for i in range(1, 25):
            if board[i][1] == player and board[i][0] == 1:
                hit = self.hit_probability(board, i, player)
                progress = 25 - pip(i, player)
                risk += hit * progress
        # The blots of the player to move are attacked only after its next move
        if player == player_to_move:
            risk *= 0.3

        return {
            'pip': sum(board[i][0] * pip(i, player) for i in range(26) if rules.owns(board, i, player)),
            'on_board': rules.checkers_left(board, player),
            'home_points': sum(made[i] for i in home),
            'anchors': sum(made[i] for i in opponent_home),
            'prime': prime,
            'bar': board[rules.bar_of(player)][0],
            'risk': risk,
        }

    @staticmethod
    def hit_probability(board, index, player):
        opponent = -player
        miss = 1.0
        for j in range(26):
            if not rules.owns(board, j, opponent):
                continue
            # The opponent moves in its own direction, so it hits only from behind the blot
            distance = (index - j) * opponent
            if distance > 0 and distance in SHOTS:
                miss *= 1 - SHOTS[distance] / 36
        return 1 - miss
