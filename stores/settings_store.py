"""The player's settings, saved with QSettings"""
from PyQt6.QtCore import QObject, QSettings, pyqtSignal

from game.config import LEVELS

SPEEDS = {'slow': 900, 'normal': 500, 'fast': 200}
DEFAULTS = {
    'show_hints': True,
    'speed': 'normal',
    'default_level': 'medium',
    'default_color': 'white',
    'default_opponent': 'computer',
}
ALLOWED = {
    'speed': set(SPEEDS),
    'default_level': set(LEVELS),
    'default_color': {'white', 'black', 'random'},
    'default_opponent': {'computer', 'friend'},
}


class SettingsStore(QObject):
    changed = pyqtSignal(str)

    def __init__(self, qsettings=None, parent=None):
        super().__init__(parent)
        self.qsettings = qsettings or QSettings('Backgammon', 'Backgammon')

    def get(self, key):
        default = DEFAULTS[key]
        value = self.qsettings.value(key, default)
        if isinstance(default, bool):
            # QSettings may hand back the strings 'true' and 'false'
            return value if isinstance(value, bool) else str(value).lower() == 'true'
        # A value that is not one of the choices falls back to the default
        return value if value in ALLOWED.get(key, {value}) else default

    def set(self, key, value):
        if self.get(key) == value:
            return
        self.qsettings.setValue(key, value)
        self.qsettings.sync()
        self.changed.emit(key)

    def step_delay_ms(self):
        return SPEEDS[self.get('speed')]
