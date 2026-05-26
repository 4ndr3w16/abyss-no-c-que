# ============================================================
# utils/math_utils.py — Pure math helpers, no pygame dependency
# ============================================================
import math


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * clamp(t, 0.0, 1.0)


def sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def distance(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(bx - ax, by - ay)


def normalize(dx: float, dy: float):
    mag = math.hypot(dx, dy)
    if mag == 0:
        return 0.0, 0.0
    return dx / mag, dy / mag


def approach(current: float, target: float, delta: float) -> float:
    """Move current toward target by at most delta."""
    diff = target - current
    if abs(diff) <= delta:
        return target
    return current + sign(diff) * delta


def rect_overlap(ax, ay, aw, ah, bx, by, bw, bh) -> bool:
    return (ax < bx + bw and ax + aw > bx and
            ay < by + bh and ay + ah > by)
