import logging
import os

from PyQt6.QtGui import QFontDatabase

log = logging.getLogger(__name__)

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts')


def load_fonts():
    """Registers the bundled fonts, returns the families that loaded"""
    families = set()
    for name in sorted(os.listdir(FONTS_DIR)):
        if not name.endswith('.ttf'):
            continue
        font_id = QFontDatabase.addApplicationFont(os.path.join(FONTS_DIR, name))
        if font_id == -1:
            log.warning('could not load the font %s', name)
            continue
        families.update(QFontDatabase.applicationFontFamilies(font_id))
    return families
