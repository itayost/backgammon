from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF
from PyQt6.QtGui import QKeySequence, QShortcut, QPainter, QColor, QPen
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QMessageBox, QDialog,
                             QSizePolicy)

import rules
from game.session import GameSession, Phase, NO_LEGAL_MOVES
from ui import theme
from ui.board.board_widget import BoardWidget, BoardView
from ui.widgets.basics import button, label, icon_button, MENU_ICON

COLOR_NAMES = {1: 'White', -1: 'Black'}


def restyle(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class CheckerChip(QWidget):
    def __init__(self, player, size=36, parent=None):
        super().__init__(parent)
        self.player = player
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        kind = 'white' if self.player == 1 else 'black'
        rim = self.width() * 0.08
        p.setPen(QPen(QColor(theme.color(f'checker-{kind}-rim')), rim))
        p.setBrush(QColor(theme.color(f'checker-{kind}')))
        r = self.width() / 2 - rim / 2
        p.drawEllipse(QPointF(self.width() / 2, self.height() / 2), r, r)
        p.end()


class PlayerCard(QFrame):
    def __init__(self, player, name, detail, parent=None):
        super().__init__(parent)
        self.player = player
        self.setProperty('role', 'player')
        self.setProperty('active', False)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(CheckerChip(player))
        names = QVBoxLayout()
        names.setSpacing(2)
        names.addWidget(label(name, 'label'))
        names.addWidget(label(detail, 'muted'))
        row.addLayout(names, 1)
        pips = QVBoxLayout()
        pips.setSpacing(0)
        self.pips = label('167', 'number')
        self.pips.setAlignment(Qt.AlignmentFlag.AlignRight)
        pips.addWidget(self.pips)
        unit = label('pips', 'muted')
        unit.setAlignment(Qt.AlignmentFlag.AlignRight)
        pips.addWidget(unit)
        row.addLayout(pips)
        outer.addLayout(row)
        self.tag = label('', 'tag')
        self.tag.setVisible(False)
        self.tag.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        outer.addWidget(self.tag)

    def update_card(self, pips, active, tag_text):
        self.pips.setText(str(pips))
        self.tag.setText(tag_text.upper())
        self.tag.setVisible(active)
        if self.property('active') != active:
            self.setProperty('active', active)
            restyle(self)


class GameScreen(QWidget):
    leave = pyqtSignal()

    def __init__(self, computer_levels, step_delay_ms=500, session=None, parent=None):
        super().__init__(parent)
        self.setObjectName('screen')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.computer_levels = dict(computer_levels)
        self.session = session or GameSession()
        self.selected = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        header = QHBoxLayout()
        header.addWidget(label('Backgammon', 'title'))
        header.addStretch(1)
        self.menu_button = icon_button(MENU_ICON, 'Menu')
        header.addWidget(self.menu_button)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(24)
        self.board = BoardWidget()
        body.addWidget(self.board, 1)

        panel = QVBoxLayout()
        panel.setSpacing(14)
        top_player = -self.bottom_player()
        self.cards = {}
        for player in (top_player, -top_player):
            card = PlayerCard(player, self.player_name(player), self.player_detail(player))
            self.cards[player] = card
            panel.addWidget(card)

        hint = QFrame()
        hint.setProperty('role', 'card')
        hint_layout = QVBoxLayout(hint)
        hint_layout.setContentsMargins(16, 16, 16, 16)
        hint_layout.setSpacing(6)
        self.hint_caption = label('', 'caption')
        self.hint_text = label('', None, wrap=True)
        # Room for three lines so the card keeps its size while the text changes
        self.hint_text.setMinimumHeight(72)
        self.hint_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        hint_layout.addWidget(self.hint_caption)
        hint_layout.addWidget(self.hint_text)
        panel.addWidget(hint)
        panel.addStretch(1)

        self.roll_button = button('Roll dice', 'primary', 52)
        self.undo_button = button('Undo', 'secondary', 52)
        self.done_button = button('Done', 'primary', 52)
        panel.addWidget(self.roll_button)
        controls = QHBoxLayout()
        controls.setSpacing(12)
        controls.addWidget(self.undo_button)
        controls.addWidget(self.done_button)
        panel.addLayout(controls)

        panel_widget = QWidget()
        panel_widget.setFixedWidth(304)
        panel_widget.setLayout(panel)
        body.addWidget(panel_widget)
        root.addLayout(body, 1)

        self.board.clicked.connect(self.on_board_click)
        self.roll_button.clicked.connect(self.roll)
        self.undo_button.clicked.connect(self.undo)
        self.done_button.clicked.connect(self.done)
        self.menu_button.clicked.connect(self.confirm_leave)
        for keys, action in (('R', self.roll), ('Space', self.roll), ('Ctrl+Z', self.undo), ('U', self.undo),
                             ('Return', self.done), ('D', self.done), ('Escape', self.confirm_leave)):
            QShortcut(QKeySequence(keys), self, action, context=Qt.ShortcutContext.WidgetWithChildrenShortcut)

        self.ai = None
        computers = {}
        if self.computer_levels:
            from ai.ai_controller import AIController
            from ai.player import ComputerPlayer
            computers = {player: ComputerPlayer(level) for player, level in self.computer_levels.items()}
            self.ai = AIController(self.session, computers, step_delay_ms=step_delay_ms)
        self.session.add_listener(self.on_event)

    def start(self):
        self.session.start()

    # Players

    def bottom_player(self):
        """The player shown at the bottom of the panel: the human against the computer, otherwise white"""
        humans = [p for p in (1, -1) if p not in self.computer_levels]
        return humans[0] if len(humans) == 1 else 1

    def is_human(self, player):
        return player not in self.computer_levels

    def player_name(self, player):
        if not self.is_human(player):
            return 'Computer'
        if len(self.computer_levels) == 1:
            return 'You'
        return 'Player 1' if player == 1 else 'Player 2'

    def player_detail(self, player):
        if not self.is_human(player):
            return f'{COLOR_NAMES[player]}, {self.computer_levels[player].capitalize()}'
        return COLOR_NAMES[player]

    def turn_tag(self, player):
        if not self.is_human(player):
            return "Computer's turn"
        if len(self.computer_levels) == 1:
            return 'Your turn'
        return f"{COLOR_NAMES[player]}'s turn"

    # Actions

    def human_turn(self):
        return self.session.phase != Phase.GAME_OVER and self.is_human(self.session.player)

    def roll(self):
        if self.human_turn():
            self.session.roll()

    def undo(self):
        if self.human_turn():
            self.selected = None
            self.session.undo()

    def done(self):
        if self.human_turn():
            self.selected = None
            self.session.end_turn()

    def on_board_click(self, kind, point):
        session = self.session
        if not self.human_turn() or session.phase != Phase.MOVING:
            return
        if kind == 'bar':
            point = rules.bar_of(session.player)
            kind = 'point'
        sources = {start for start, _ in session.legal}
        if kind == 'point':
            if self.selected is None:
                if point in sources:
                    self.selected = point
            elif point == self.selected:
                self.selected = None
            elif point in self.targets():
                start, self.selected = self.selected, None
                session.move(start, abs(point - start))
                return
            elif point in sources:
                self.selected = point
        elif kind == 'tray' and self.selected is not None:
            jumps = [jump for start, jump in session.legal
                     if start == self.selected and session.destination(start, jump) is None]
            if jumps:
                start, self.selected = self.selected, None
                session.move(start, min(jumps))
                return
        self.refresh()

    def targets(self):
        if self.selected is None:
            return set()
        return {self.session.destination(start, jump) for start, jump in self.session.legal
                if start == self.selected} - {None}

    def confirm_leave(self):
        answer = QMessageBox.question(self, 'Leave the game', 'Leaving ends this game. Go to the main menu?')
        if answer == QMessageBox.StandardButton.Yes:
            self.leave.emit()

    # Session events

    def on_event(self, event, data):
        if event in ('game_started', 'turn_started', 'stepped', 'undone'):
            self.selected = None
        self.refresh()
        if event == 'game_over':
            QTimer.singleShot(0, self.show_result)

    def show_result(self):
        from winner_dialog import WinnerDialog
        winner = self.session.stats.winner
        name = self.player_name(winner)
        title = 'You' if name == 'You' else ('The computer' if name == 'Computer' else COLOR_NAMES[winner])
        dialog = WinnerDialog(title, self)
        if dialog.exec() == QDialog.DialogCode.Accepted.value:
            self.start()
        else:
            self.leave.emit()

    def shutdown(self):
        if self.ai is not None:
            self.ai.stop()
        self.session.remove_listener(self.on_event)

    # Drawing the state

    def dice_view(self):
        left = list(self.session.dice_left)
        view = []
        for value in reversed(self.session.dice):
            if value in left:
                left.remove(value)
                view.append((value, False))
            else:
                view.append((value, True))
        return list(reversed(view))

    def refresh(self):
        session = self.session
        human = self.human_turn()
        moving = human and session.phase == Phase.MOVING
        sources = {start for start, _ in session.legal} if moving else set()
        selected = self.selected if moving else None
        targets = self.targets() if moving else set()
        tray = moving and selected is not None and any(
            start == selected and session.destination(start, jump) is None for start, jump in session.legal)
        self.board.set_view(BoardView(board=[cell[:] for cell in session.board], dice=self.dice_view(),
                                      sources=sources, selected=selected, targets=targets,
                                      tray_target=tray, player=session.player))

        for player, card in self.cards.items():
            active = session.phase != Phase.GAME_OVER and player == session.player
            card.update_card(session.pips(player), active, self.turn_tag(player))

        self.hint_caption.setText(self.hint_caption_text().upper())
        self.hint_text.setText(self.hint_body_text())

        awaiting = human and session.phase == Phase.AWAIT_ROLL
        self.roll_button.setVisible(awaiting)
        self.undo_button.setVisible(not awaiting)
        self.done_button.setVisible(not awaiting)
        self.undo_button.setEnabled(human and session.can_undo())
        ready = human and session.phase == Phase.READY_TO_END
        self.done_button.setEnabled(ready)

    def hint_caption_text(self):
        session = self.session
        player = COLOR_NAMES[session.player]
        if session.phase == Phase.GAME_OVER:
            return 'Game over'
        if session.opening is not None:
            white, black = session.opening
            return f'White rolled {white}, black rolled {black}'
        if session.phase == Phase.AWAIT_ROLL:
            return self.turn_tag(session.player)
        dice = ' and '.join(str(d) for d in session.dice[:2]) if len(set(session.dice)) > 1 \
            else f'double {session.dice[0]}'
        who = 'You' if self.player_name(session.player) == 'You' else (
            'The computer' if not self.is_human(session.player) else player)
        return f'{who} rolled {dice}'

    def hint_body_text(self):
        session = self.session
        if session.phase == Phase.GAME_OVER:
            return f'{COLOR_NAMES[session.stats.winner]} won.'
        starts = f'{COLOR_NAMES[session.player]} starts. ' if session.opening is not None else ''
        if not self.is_human(session.player):
            return starts + ('Rolling the dice.' if session.phase == Phase.AWAIT_ROLL else 'Thinking and moving.')
        if session.phase == Phase.AWAIT_ROLL:
            return 'Roll the dice to start the turn.'
        if session.phase == Phase.READY_TO_END:
            if session.reason == NO_LEGAL_MOVES:
                return starts + 'There is no legal move with these dice. Press Done to pass the turn.'
            return 'All the dice you can play are used. Press Done to end the turn, or Undo to change it.'
        if self.selected is not None:
            return starts + 'Click a highlighted point to move there, or the checker again to cancel.'
        return starts + 'Select a checker, then a highlighted point.'
