import logging
import time

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

import rules
from ai.search import choose_move

log = logging.getLogger(__name__)


class ThinkingThread(QThread):
    done = pyqtSignal(int, object)

    def __init__(self, computer, board, player, dice, generation):
        super().__init__()
        self.computer = computer
        self.board = board
        self.player = player
        self.dice = dice
        self.generation = generation

    def run(self):
        start = time.monotonic()
        try:
            steps = self.computer.choose(self.board, self.player, self.dice)
        except Exception:
            log.exception('the computer failed to choose a move')
            steps = None
        log.debug('computer thought %.2fs', time.monotonic() - start)
        self.done.emit(self.generation, steps)


class AIController(QObject):
    """Plays for the computer players. It listens to the model like the gui does,
    thinks in a background thread and sends the chosen steps one by one like clicks."""

    def __init__(self, model, computers, step_delay_ms=500):
        super().__init__()
        self.model = model
        self.computers = computers  # player (1 or -1) -> ComputerPlayer
        self.generation = 0
        self.player = None
        self.steps = []
        self.threads = set()
        self.timer = QTimer(self)
        self.timer.setInterval(step_delay_ms)
        self.timer.timeout.connect(self.play_step)
        self.model.add_controller(self)

    def cancel(self):
        # Results and steps of an older generation are dropped
        self.generation += 1
        self.steps = []
        self.player = None
        self.timer.stop()

    def to_gui_new_game(self, board):
        self.cancel()

    def to_gui_new_turn(self, player, dice, moves):
        self.cancel()
        if player not in self.computers:
            return
        self.player = player
        thread = ThinkingThread(self.computers[player], rules.copy_board(self.model.board), player, list(dice),
                                self.generation)
        thread.done.connect(self.on_thought)
        thread.finished.connect(lambda: self.threads.discard(thread))
        self.threads.add(thread)
        thread.start()

    def on_thought(self, generation, steps):
        if generation != self.generation:
            return
        self.steps = list(steps) if steps else []
        self.timer.start()

    def play_step(self):
        generation = self.generation
        if not self.steps:
            # The plan ended or failed but it is still the computer's turn, continue with a quick choice
            self.steps = self.fallback_steps()
            if not self.steps:
                self.timer.stop()
                return
        position, jump = self.steps.pop(0)
        # A move that ends the turn or the game starts a new generation before get_move returns
        if not self.model.get_move(position, jump) and generation == self.generation:
            log.error('the model rejected the computer move %s', (position, jump))
            self.steps = []

    def fallback_steps(self):
        if self.player is None or not self.model.moves:
            return []
        steps = choose_move(self.model.board, self.player, self.model.dice, self.computers[self.player].evaluator)
        if steps and steps[0] in self.model.moves:
            return steps
        return [self.model.moves[0]]

    def wait_for_threads(self):
        for thread in list(self.threads):
            thread.wait()

    # The model sends these to every listener, the computer does not need them
    def to_gui_new_move(self, moves_made, moves_available, dice):
        pass

    def to_gui_throw_made(self, position, moves_available, dice):
        pass

    def to_gui_winner(self, player):
        pass

    def to_gui_no_moves(self, player, dice):
        pass
