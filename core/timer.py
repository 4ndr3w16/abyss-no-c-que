# ============================================================
# core/timer.py — Frame-independent countdown timers
# ============================================================

class Timer:
    """Simple countdown timer. Call update(dt) each frame."""

    def __init__(self, duration: float = 0.0, active: bool = False):
        self.duration = duration
        self._elapsed = 0.0
        self.active = active

    def start(self, duration: float | None = None):
        if duration is not None:
            self.duration = duration
        self._elapsed = 0.0
        self.active = True

    def update(self, dt: float):
        if self.active:
            self._elapsed += dt
            if self._elapsed >= self.duration:
                self.active = False

    @property
    def done(self) -> bool:
        return not self.active

    @property
    def progress(self) -> float:
        """0.0 → 1.0 completion ratio."""
        if self.duration == 0:
            return 1.0
        return min(self._elapsed / self.duration, 1.0)

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration - self._elapsed)


class CooldownTimer(Timer):
    """Like Timer but semantics: ready when done."""

    def __init__(self, duration: float = 0.0):
        super().__init__(duration, active=False)

    @property
    def ready(self) -> bool:
        return self.done
