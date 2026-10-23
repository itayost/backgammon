"""The Midnight Felt design tokens from DESIGN.md and the Qt stylesheet built from them.

DESIGN.md is the source of truth: tests/test_theme.py fails when a value here drifts from it.
"""

COLORS = {
    'bg': '#0E1617',
    'surface': '#162224',
    'surface-2': '#1E2E30',
    'line': '#2C4144',
    'text': '#EEE7D9',
    'text-muted': '#9DB0AD',
    'text-disabled': '#6F8380',
    'accent': '#F0A73A',
    'accent-hover': '#F5BC66',
    'accent-ink': '#1A1206',
    'danger': '#F08A7E',
    'danger-surface': '#2A1A19',
    'danger-line': '#5A2A26',
    'success': '#8FD3A8',
    'board-frame': '#3B2A1E',
    'board-bar': '#2E2016',
    'board-felt': '#1F4A44',
    'point-light': '#D9CDB4',
    'point-dark': '#A8473A',
    'checker-white': '#F4EFE4',
    'checker-white-rim': '#C9BFAE',
    'checker-black': '#1C1C1E',
    'checker-black-rim': '#4A4A50',
    'scrim': 'rgba(5, 10, 11, 0.72)',
}

DISPLAY_FONT = 'Outfit'
BODY_FONT = 'Inter'

# The bundled static fonts register one family per weight
FAMILIES = {
    (BODY_FONT, 400): 'Inter',
    (BODY_FONT, 500): 'Inter Medium',
    (BODY_FONT, 600): 'Inter SemiBold',
    (DISPLAY_FONT, 500): 'Outfit Medium',
    (DISPLAY_FONT, 600): 'Outfit SemiBold',
    (DISPLAY_FONT, 700): 'Outfit',
}


def font_css(family, weight):
    return f'font-family: "{FAMILIES[(family, weight)]}"; font-weight: {weight};'

# name: (family, size px, weight, line height px)
TYPE = {
    'display': (DISPLAY_FONT, 56, 700, 64),
    'headline': (DISPLAY_FONT, 32, 600, 40),
    'title': (DISPLAY_FONT, 22, 600, 28),
    'number': (DISPLAY_FONT, 28, 600, 32),
    'body': (BODY_FONT, 16, 400, 24),
    'label': (BODY_FONT, 14, 500, 20),
    'caption': (BODY_FONT, 12, 600, 16),
}

RADIUS = {'sm': 6, 'segment': 8, 'md': 10, 'choice': 12, 'lg': 16, 'pill': 999}
SPACING = [4, 8, 12, 16, 24, 32, 48, 64]

# A widget picks its look with setProperty('variant', ...) or its object name
VARIANTS = ('primary', 'secondary', 'ghost', 'danger', 'icon')


def color(name):
    return COLORS[name]


def stylesheet():
    c = COLORS
    return f"""
QMainWindow, QStackedWidget, QWidget#screen {{
    background: {c['bg']};
}}
QWidget {{
    color: {c['text']};
    {font_css(BODY_FONT, 400)}
    font-size: 16px;
}}
QToolTip {{
    background: {c['surface-2']};
    color: {c['text']};
    border: 1px solid {c['line']};
    padding: 6px 8px;
}}

QLabel[role="display"] {{ {font_css(DISPLAY_FONT, 700)} font-size: 56px; }}
QLabel[role="wordmark"] {{ {font_css(DISPLAY_FONT, 700)} font-size: 80px; }}
QLabel[role="headline"] {{ {font_css(DISPLAY_FONT, 600)} font-size: 32px; }}
QLabel[role="title"] {{ {font_css(DISPLAY_FONT, 600)} font-size: 22px; }}
QLabel[role="big-number"] {{ {font_css(DISPLAY_FONT, 600)} font-size: 44px; }}
QLabel[role="number"] {{ {font_css(DISPLAY_FONT, 600)} font-size: 28px; }}
QLabel[role="lead"] {{ font-size: 18px; color: {c['text-muted']}; }}
QLabel[role="label"] {{ {font_css(BODY_FONT, 500)} font-size: 14px; }}
QLabel[role="muted"] {{ font-size: 14px; color: {c['text-muted']}; }}
QLabel[role="caption"] {{ {font_css(BODY_FONT, 600)} font-size: 12px; letter-spacing: 1px; color: {c['text-muted']}; }}
QLabel[role="kicker"] {{ {font_css(BODY_FONT, 600)} font-size: 12px; letter-spacing: 1px; color: {c['accent']}; }}

QFrame[role="card"] {{
    background: {c['surface']};
    border: 1px solid {c['line']};
    border-radius: {RADIUS['lg']}px;
}}
QFrame[role="dialog"] {{
    background: {c['surface']};
    border: 1px solid {c['line']};
    border-radius: {RADIUS['lg']}px;
}}
QFrame[role="tile"] {{
    background: {c['surface-2']};
    border: 0;
    border-radius: {RADIUS['md']}px;
}}
QLabel[role="result-win"] {{ {font_css(DISPLAY_FONT, 700)} font-size: 56px; color: {c['success']}; }}
QLabel[role="result"] {{ {font_css(DISPLAY_FONT, 700)} font-size: 56px; }}
QFrame[role="player"] {{
    background: {c['surface']};
    border: 2px solid {c['line']};
    border-radius: {RADIUS['lg']}px;
}}
QFrame[role="player"][active="true"] {{ border-color: {c['accent']}; }}
QLabel[role="tag"] {{
    background: {c['accent']};
    color: {c['accent-ink']};
    border-radius: 10px;
    padding: 3px 10px;
    {font_css(BODY_FONT, 600)}
    font-size: 12px;
    letter-spacing: 1px;
}}
QFrame[role="divider"] {{
    background: {c['line']};
    border: 0;
    max-height: 1px;
    min-height: 1px;
}}

QDialog {{
    background: {c['surface']};
}}
QComboBox {{
    min-height: 40px;
    padding: 0 12px;
    background: {c['surface-2']};
    border: 1px solid {c['line']};
    border-radius: {RADIUS['segment']}px;
}}
QComboBox:focus {{ border-color: {c['accent']}; }}
QComboBox QAbstractItemView {{
    background: {c['surface-2']};
    color: {c['text']};
    selection-background-color: {c['accent']};
    selection-color: {c['accent-ink']};
}}

QPushButton {{
    min-height: 44px;
    padding: 0 24px;
    border-radius: {RADIUS['md']}px;
    background: {c['surface-2']};
    color: {c['text']};
    border: 2px solid {c['line']};
    font-size: 16px;
    {font_css(BODY_FONT, 600)}
}}
QPushButton:hover {{ background: #24373A; }}
QPushButton[variant="primary"] {{
    background: {c['accent']};
    color: {c['accent-ink']};
    border-color: transparent;
}}
QPushButton[variant="primary"]:hover {{ background: {c['accent-hover']}; }}
QPushButton[variant="primary"]:focus {{ border-color: {c['text']}; }}
QPushButton[variant="secondary"] {{
    background: {c['surface-2']};
    color: {c['text']};
    border: 2px solid {c['line']};
}}
QPushButton[variant="secondary"]:hover {{ background: #24373A; }}
QPushButton[variant="ghost"] {{
    background: transparent;
    color: {c['text-muted']};
    border-color: transparent;
    {font_css(BODY_FONT, 500)}
}}
QPushButton[variant="ghost"]:hover {{ background: transparent; color: {c['text']}; }}
QPushButton[variant="danger"] {{
    background: {c['danger-surface']};
    color: {c['danger']};
    border: 2px solid {c['danger-line']};
}}
QPushButton[variant="danger"]:hover {{ background: #331F1D; }}
QPushButton[variant="icon"] {{
    min-height: 44px;
    max-height: 44px;
    min-width: 44px;
    max-width: 44px;
    padding: 0;
    background: {c['surface-2']};
    border: 2px solid {c['line']};
}}
QPushButton[variant="icon"]:hover {{ background: #24373A; }}
QFrame[role="segments"] {{
    background: {c['bg']};
    border: 1px solid {c['line']};
    border-radius: {RADIUS['choice']}px;
}}
QPushButton[variant="segment"] {{
    min-height: 40px;
    padding: 0 20px;
    border-radius: {RADIUS['segment']}px;
    border: 2px solid transparent;
    background: transparent;
    color: {c['text-muted']};
    {font_css(BODY_FONT, 500)}
    font-size: 15px;
}}
QPushButton[variant="segment"]:hover {{ background: transparent; color: {c['text']}; }}
QPushButton[variant="segment"]:checked {{
    background: {c['accent']};
    color: {c['accent-ink']};
    {font_css(BODY_FONT, 600)}
}}
QPushButton[variant="segment"]:checked:focus {{ border-color: {c['text']}; }}
QPushButton[variant="choice"] {{
    min-height: 56px;
    padding: 0;
    text-align: left;
    background: {c['surface']};
    border: 2px solid {c['line']};
    border-radius: {RADIUS['choice']}px;
}}
QPushButton[variant="choice"][tall="true"] {{ min-height: 84px; }}
QPushButton[variant="choice"]:hover {{ background: {c['surface-2']}; }}
QPushButton[variant="choice"]:checked {{
    background: {c['surface-2']};
    border-color: {c['accent']};
}}
QPushButton[variant="choice"]:focus {{ border-color: {c['text']}; }}
QPushButton[variant="choice"]:checked:focus {{ border-color: {c['accent-hover']}; }}
QLabel[role="choice-title"] {{ {font_css(BODY_FONT, 600)} font-size: 16px; background: transparent; }}
QPushButton[variant="switch"] {{
    min-height: 30px;
    max-height: 30px;
    min-width: 52px;
    max-width: 52px;
    padding: 0;
    border: 0;
    background: transparent;
}}
QPushButton:focus {{ border-color: {c['accent']}; }}
QPushButton:disabled {{
    background: {c['surface-2']};
    color: {c['text-disabled']};
    border-color: transparent;
}}
"""
