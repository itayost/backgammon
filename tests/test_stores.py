import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stores.stats_store import StatsStore  # noqa: E402


class StatsStoreTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, 'nested', 'stats.json')

    def tearDown(self):
        self.folder.cleanup()

    def test_starts_empty(self):
        stats = StatsStore(self.path)
        self.assertEqual(stats.computer_games(), 0)
        self.assertEqual(stats.level('hard'), {'wins': 0, 'losses': 0, 'streak': 0})

    def test_wins_losses_and_streaks(self):
        stats = StatsStore(self.path)
        for won in (True, True, False, False, False, True):
            stats.record_computer_game('medium', won)
        self.assertEqual(stats.level('medium'), {'wins': 3, 'losses': 3, 'streak': 1})
        stats.record_computer_game('medium', False)
        self.assertEqual(stats.level('medium')['streak'], -1)
        self.assertEqual(stats.computer_games(), 7)
        self.assertEqual(stats.computer_wins(), 3)

    def test_saved_between_runs(self):
        stats = StatsStore(self.path)
        stats.record_computer_game('easy', True)
        stats.record_friend_game()
        again = StatsStore(self.path)
        self.assertEqual(again.level('easy')['wins'], 1)
        self.assertEqual(again.friend_games(), 1)
        self.assertFalse(os.path.exists(self.path + '.tmp'))

    def test_reset(self):
        stats = StatsStore(self.path)
        stats.record_computer_game('hard', False)
        stats.reset()
        self.assertEqual(StatsStore(self.path).computer_games(), 0)

    def test_damaged_file_is_set_aside(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, 'w') as f:
            f.write('{not json')
        stats = StatsStore(self.path)
        self.assertEqual(stats.computer_games(), 0)
        self.assertTrue(os.path.exists(self.path + '.bad'))

    def test_unknown_and_missing_fields(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, 'w') as f:
            json.dump({'version': 1, 'levels': {'easy': {'wins': 2}, 'expert': {'wins': 9}}, 'other': 1}, f)
        stats = StatsStore(self.path)
        self.assertEqual(stats.level('easy'), {'wins': 2, 'losses': 0, 'streak': 0})
        self.assertEqual(stats.computer_games(), 2)


try:
    from PyQt6.QtCore import QSettings
except ImportError:
    QSettings = None


@unittest.skipIf(QSettings is None, 'PyQt6 is not installed')
class SettingsStoreTest(unittest.TestCase):
    def setUp(self):
        from stores.settings_store import SettingsStore
        self.folder = tempfile.TemporaryDirectory()
        self.file = os.path.join(self.folder.name, 'settings.ini')
        self.store = SettingsStore(QSettings(self.file, QSettings.Format.IniFormat))

    def tearDown(self):
        self.folder.cleanup()

    def test_defaults(self):
        self.assertTrue(self.store.get('show_hints'))
        self.assertEqual(self.store.get('speed'), 'normal')
        self.assertEqual(self.store.step_delay_ms(), 500)

    def test_saved_between_runs(self):
        from stores.settings_store import SettingsStore
        changes = []
        self.store.changed.connect(changes.append)
        self.store.set('show_hints', False)
        self.store.set('speed', 'fast')
        self.store.set('speed', 'fast')
        self.assertEqual(changes, ['show_hints', 'speed'])
        again = SettingsStore(QSettings(self.file, QSettings.Format.IniFormat))
        self.assertFalse(again.get('show_hints'))
        self.assertEqual(again.step_delay_ms(), 200)

    def test_bad_value_falls_back(self):
        self.store.qsettings.setValue('default_level', 'impossible')
        self.assertEqual(self.store.get('default_level'), 'medium')


if __name__ == '__main__':
    unittest.main()
