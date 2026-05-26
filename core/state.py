# ============================================================
# core/state.py — State machine for game screens / modes
# ============================================================
from enum import Enum, auto


class GameState(Enum):
    MAIN_MENU  = auto()
    CONTROLS   = auto()
    PLAYING    = auto()
    PAUSED     = auto()
    ROOM_TRANS = auto()
    GAME_OVER  = auto()
    VICTORY    = auto()


class StateMachine:
    def __init__(self, initial: GameState):
        self.current  = initial
        self._previous = initial
        self._handlers: dict[GameState, object] = {}

    def register(self, state: GameState, handler):
        self._handlers[state] = handler

    def transition(self, new_state: GameState):
        self._previous = self.current
        self.current   = new_state

    def get_handler(self):
        return self._handlers.get(self.current)

    @property
    def previous(self) -> GameState:
        return self._previous
