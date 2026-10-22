"""Board geometry in logical units, the 904 x 692 board of the mockup.
The widget scales these to its size; hit testing works in the same units."""

W, H = 904, 692
PAD = 14
GAP = 10
BAR_W = 44
TRAY_W = 56
FIELD_W = (W - 2 * PAD - BAR_W - TRAY_W - 3 * GAP) / 2
LEFT_X = PAD
BAR_X = LEFT_X + FIELD_W + GAP
RIGHT_X = BAR_X + BAR_W + GAP
TRAY_X = RIGHT_X + FIELD_W + GAP
FIELD_PAD = 10
POINT_GAP = 4
POINT_W = (FIELD_W - 2 * FIELD_PAD - 5 * POINT_GAP) / 6
ROW_H = 280
TOP_Y = PAD + FIELD_PAD
BOTTOM_Y = H - PAD - FIELD_PAD - ROW_H
MID_Y = H / 2

CHECKER = 50
STACK_STEP = 51
MAX_SHOWN = 5
BAR_CHECKER = 42
BAR_STEP = 44
DIE = 48
DIE_GAP = 12
SLAB_H = 10
SLAB_STEP = 12


def point_rect(point):
    """(x, y, width, height, is_top) of a point's triangle area.
    Top row left to right: 12..7 | 6..1, bottom row: 13..18 | 19..24 (white's home bottom right)."""
    if 1 <= point <= 6:
        field_x, column, top = RIGHT_X, 6 - point, True
    elif 7 <= point <= 12:
        field_x, column, top = LEFT_X, 12 - point, True
    elif 13 <= point <= 18:
        field_x, column, top = LEFT_X, point - 13, False
    elif 19 <= point <= 24:
        field_x, column, top = RIGHT_X, point - 19, False
    else:
        raise ValueError(point)
    x = field_x + FIELD_PAD + column * (POINT_W + POINT_GAP)
    return x, TOP_Y if top else BOTTOM_Y, POINT_W, ROW_H, top


def checker_center(point, slot):
    """Center of the checker in a stack slot, slot 0 sits at the board edge"""
    x, y, w, h, top = point_rect(point)
    cx = x + w / 2
    offset = CHECKER / 2 + slot * STACK_STEP
    return cx, (y + offset) if top else (y + h - offset)


def bar_center(player, slot):
    """White waits on the top half of the bar, black on the bottom half"""
    cx = BAR_X + BAR_W / 2
    offset = 34 + slot * BAR_STEP
    return cx, (MID_Y - offset) if player == 1 else (MID_Y + offset)


def tray_rect(player):
    """White bears off into the bottom half of the tray, next to its home, black into the top half"""
    half = (H - 2 * PAD) / 2
    if player == 1:
        return TRAY_X, PAD + half, TRAY_W, half
    return TRAY_X, PAD, TRAY_W, half


def slab_rect(player, index):
    x = TRAY_X + 8
    if player == 1:
        return x, H - PAD - 34 - (index + 1) * SLAB_STEP, TRAY_W - 16, SLAB_H
    return x, PAD + 34 + index * SLAB_STEP, TRAY_W - 16, SLAB_H


def dice_centers(count):
    total = count * DIE + (count - 1) * DIE_GAP
    start = RIGHT_X + FIELD_W / 2 - total / 2 + DIE / 2
    return [(start + i * (DIE + DIE_GAP), MID_Y) for i in range(count)]


def hit_test(x, y):
    """What was clicked: ('point', n), ('bar', None), ('tray', None) or None"""
    for point in range(1, 25):
        px, py, w, h, _ = point_rect(point)
        if px <= x <= px + w and py <= y <= py + h:
            return 'point', point
    if BAR_X <= x <= BAR_X + BAR_W and PAD <= y <= H - PAD:
        return 'bar', None
    if TRAY_X <= x <= TRAY_X + TRAY_W and PAD <= y <= H - PAD:
        return 'tray', None
    return None
