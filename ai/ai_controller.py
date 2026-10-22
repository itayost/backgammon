import logging
import time

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

import rules
from ai.search import choose_move
from game.session import Phase

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
    """Plays for the computer players of a GameSession: rolls, thinks in a background thread,
    plays the chosen steps one by one with a pause between them, and ends the turn.

    Every scheduled action carries the generation it was planned in; a new game, a new turn or
    the end of the game starts a new generation, so anything planned before is dropped."""

    def __init__(self, session, computers, step_delay_ms=500, roll_delay_ms=400):
        super().__init__()
        self.session = session
        self.computers = computers  # player (1 or -1) -> ComputerPlayer
        self.step_delay_ms = step_delay_ms
        self.roll_delay_ms = roll_delay_ms
        self.generation = 0
        self.paused = False
        self.pending = None
        self.steps = []
        self.threads = set()
        self.session.add_listener(self.on_event)

    def on_event(self, event, data):
        if event in ('game_started', 'turn_started', 'game_over'):
            self.cancel()
        if event in ('game_started', 'turn_started'):
            self.later(self.check, 0)

    def cancel(self):
        self.generation += 1
        self.steps = []
        self.pending = None

    def stop(self):
        """Detaches from the session and waits for any thinking to end"""
        self.cancel()
        self.session.remove_listener(self.on_event)
        for thread in list(self.threads):
            thread.wait()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        if self.pending is not None:
            generation, action = self.pending
            self.pending = None
            self.run_if_current(generation, action)

    def later(self, action, delay_ms):
        generation = self.generation
        QTimer.singleShot(delay_ms, lambda: self.run_if_current(generation, action))

    def run_if_current(self, generation, action):
        if generation != self.generation:
            return
        if self.paused:
            self.pending = (generation, action)
            return
        action()

    def check(self):
        """Does the next thing the computer has to do in its turn"""
        session = self.session
        if session.phase == Phase.GAME_OVER or session.player not in self.computers:
            return
        if session.phase == Phase.AWAIT_ROLL:
            self.later(self.roll, self.roll_delay_ms)
        elif session.phase == Phase.MOVING:
            self.think()
        elif session.phase == Phase.READY_TO_END:
            self.later(session.end_turn, self.step_delay_ms)

    def roll(self):
        self.session.roll()
        # Leave the dice on screen for a moment before moving
        self.later(self.check, self.roll_delay_ms)

    def think(self):
        session = self.session
        thread = ThinkingThread(self.computers[session.player], rules.copy_board(session.board),
                                session.player, list(session.dice_left), self.generation)
        thread.done.connect(self.on_thought)
        thread.finished.connect(lambda: self.threads.discard(thread))
        self.threads.add(thread)
        thread.start()

    def on_thought(self, generation, steps):
        if generation != self.generation:
            return
        self.steps = list(steps) if steps is not None else self.quick_steps()
        self.later(self.play_step, self.step_delay_ms)

    def quick_steps(self):
        """A fast 1-ply choice when the thinking failed, the first legal move if even that fails"""
        session = self.session
        try:
            return choose_move(session.board, session.player, session.dice_left,
                               self.computers[session.player].evaluator)
        except Exception:
            log.exception('the quick choice failed too')
            return [session.legal[0]] if session.legal else []

    def play_step(self):
        session = self.session
        if session.phase != Phase.MOVING:
            self.check()
            return
        generation = self.generation
        step = self.steps.pop(0) if self.steps else None
        if step is None or not session.move(*step):
            if step is not None:
                log.error('the session rejected the computer move %s', step)
            self.steps = self.quick_steps()
            if not self.steps or not session.move(*self.steps.pop(0)):
                return
        # Winning the game ends the generation while the move is played
        if generation != self.generation or session.phase == Phase.GAME_OVER:
            return
        self.later(self.play_step if self.steps else self.check, self.step_delay_ms)
