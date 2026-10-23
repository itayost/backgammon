"""Wins and losses against the computer per level, and the number of games with a friend, in a JSON file"""
import json
import logging
import os

from game.config import LEVELS

log = logging.getLogger(__name__)
VERSION = 1


def empty_stats():
    return {'version': VERSION,
            'levels': {level: {'wins': 0, 'losses': 0, 'streak': 0} for level in LEVELS},
            'friend_games': 0}


class StatsStore:
    def __init__(self, path):
        self.path = path
        self.data = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return empty_stats()
        try:
            with open(self.path, encoding='utf-8') as f:
                data = json.load(f)
            # Keep only what this version knows, so a hand edited or older file still loads
            stats = empty_stats()
            for level in LEVELS:
                saved = data['levels'].get(level, {})
                for key in ('wins', 'losses', 'streak'):
                    stats['levels'][level][key] = int(saved.get(key, 0))
            stats['friend_games'] = int(data.get('friend_games', 0))
            return stats
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            log.warning('the statistics file %s is damaged, starting over', self.path)
            try:
                os.replace(self.path, self.path + '.bad')
            except OSError:
                pass
            return empty_stats()

    def save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        temporary = self.path + '.tmp'
        with open(temporary, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
        # Replacing in one step means a crash never leaves a half written file
        os.replace(temporary, self.path)

    def record_computer_game(self, level, won):
        entry = self.data['levels'][level]
        if won:
            entry['wins'] += 1
            entry['streak'] = entry['streak'] + 1 if entry['streak'] > 0 else 1
        else:
            entry['losses'] += 1
            entry['streak'] = entry['streak'] - 1 if entry['streak'] < 0 else -1
        self.save()

    def record_friend_game(self):
        self.data['friend_games'] += 1
        self.save()

    def reset(self):
        self.data = empty_stats()
        self.save()

    def level(self, level):
        return dict(self.data['levels'][level])

    def computer_games(self):
        return sum(e['wins'] + e['losses'] for e in self.data['levels'].values())

    def computer_wins(self):
        return sum(e['wins'] for e in self.data['levels'].values())

    def friend_games(self):
        return self.data['friend_games']
