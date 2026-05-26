# ============================================================
# systems/combat.py — Hit detection, damage resolution, combos
# ============================================================
import pygame
from settings import *
from core.timer import CooldownTimer, Timer
from utils.math_utils import clamp


class HitEvent:
    """Data produced when a hit lands; consumed by effect/audio systems."""
    __slots__ = ('attacker', 'target', 'damage', 'hx', 'hy', 'combo')

    def __init__(self, attacker, target, damage, hx, hy, combo=1):
        self.attacker = attacker
        self.target   = target
        self.damage   = damage
        self.hx, self.hy = hx, hy
        self.combo    = combo


class AttackState:
    """
    Tracks one swing's lifecycle: startup → active → recovery.
    Times are in seconds.
    """
    def __init__(self, duration, active_start, active_end, damage,
                 reach, height, facing, origin_getter):
        self.duration     = duration
        self.active_start = active_start
        self.active_end   = active_end
        self.base_damage  = damage
        self.reach        = reach
        self.height       = height
        self.facing       = facing          # +1 or -1
        self._origin      = origin_getter   # callable → (cx, cy)
        self._t           = 0.0
        self.hit_targets: set = set()       # prevent multi-hitting same target

    def update(self, dt) -> bool:
        """Returns True while still active."""
        self._t += dt
        return self._t < self.duration

    @property
    def in_active_window(self) -> bool:
        return self.active_start <= self._t <= self.active_end

    def get_hitbox(self) -> pygame.Rect:
        cx, cy = self._origin()
        x = cx if self.facing > 0 else cx - self.reach * 2
        return pygame.Rect(x, cy - self.height // 2,
                           self.reach * 2, self.height)


class ComboTracker:
    def __init__(self):
        self.count   = 0
        self._window = 0.0          # time remaining to extend combo

    def register_hit(self):
        self.count   = min(self.count + 1, MAX_COMBO)
        self._window = COMBO_WINDOW

    def update(self, dt):
        if self._window > 0:
            self._window -= dt
            if self._window <= 0:
                self.count = 0

    @property
    def damage_mult(self) -> float:
        idx = clamp(self.count - 1, 0, len(COMBO_DAMAGE_MULT) - 1)
        return COMBO_DAMAGE_MULT[idx]

    def reset(self):
        self.count   = 0
        self._window = 0.0


# ── Public API used by game loop ──────────────────────────────

def resolve_attacks(attacker_list, defender_list) -> list[HitEvent]:
    """
    Check each active AttackState against defenders.
    Returns list of HitEvents (deduped per target per swing).
    """
    events = []
    for atk in attacker_list:
        attack = getattr(atk, 'current_attack', None)
        if attack is None or not attack.in_active_window:
            continue
        hbox = attack.get_hitbox()
        for dfn in defender_list:
            if dfn in attack.hit_targets:
                continue
            if not dfn.alive:
                continue
            if hbox.colliderect(dfn.rect):
                attack.hit_targets.add(dfn)
                combo = getattr(atk, 'combo', None)
                mult  = combo.damage_mult if combo else 1.0
                raw   = int(attack.base_damage * mult)
                cx    = hbox.centerx
                cy    = hbox.centery
                c_idx = combo.count if combo else 1
                events.append(HitEvent(atk, dfn, raw, cx, cy, c_idx))
    return events


def apply_hit_events(events: list[HitEvent], effects=None):
    for ev in events:
        ev.target.take_damage(ev.damage)
        if effects:
            effects.hit_sparks(ev.hx, ev.hy)
            effects.damage_number(ev.hx, ev.hy - 20, ev.damage, ev.combo)
        attacker_combo = getattr(ev.attacker, 'combo', None)
        if attacker_combo:
            attacker_combo.register_hit()
