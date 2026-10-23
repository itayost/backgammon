import random
from dataclasses import dataclass

LEVELS = ('easy', 'medium', 'hard')
COLORS = {'white': 1, 'black': -1}


@dataclass
class GameConfig:
    """What the New game screen chose. color is the human's color ('white', 'black' or 'random');
    with a friend it is player 1's color."""
    opponent: str = 'computer'   # 'computer', 'friend' or 'self_play' (computer against computer)
    level: str = 'medium'
    color: str = 'white'

    def resolve_color(self, rng=random):
        """The human's color as 1 or -1, a random color is drawn again for every game"""
        if self.color == 'random':
            return rng.choice([1, -1])
        return COLORS[self.color]

    def computer_levels(self, rng=random):
        """Maps every player the computer plays to its level for one game"""
        if self.opponent == 'friend':
            return {}
        if self.opponent == 'self_play':
            return {1: self.level, -1: self.level}
        return {-self.resolve_color(rng): self.level}
