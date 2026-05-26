# ============================================================
# systems/movement.py — Physics integration & tile collision
# ============================================================
import pygame
from settings import *
from utils.math_utils import clamp, sign


def move_and_collide(entity, walls: list[pygame.Rect], dt: float):
    """
    Apply entity.vx / entity.vy, resolve AABB against wall list.
    entity must have: rect (pygame.Rect), vx, vy, on_ground (bool)
    """
    rect = entity.rect

    # ── Horizontal ──────────────────────────────────────────
    rect.x += int(entity.vx * dt)
    for wall in walls:
        if rect.colliderect(wall):
            if entity.vx > 0:
                rect.right = wall.left
            elif entity.vx < 0:
                rect.left = wall.right
            entity.vx = 0

    # ── Vertical ────────────────────────────────────────────
    rect.y += int(entity.vy * dt)
    entity.on_ground = False
    for wall in walls:
        if rect.colliderect(wall):
            if entity.vy > 0:
                rect.bottom = wall.top
                entity.on_ground = True
            elif entity.vy < 0:
                rect.top = wall.bottom
            entity.vy = 0


def apply_gravity(entity, dt: float):
    entity.vy += GRAVITY * dt
    entity.vy  = min(entity.vy, 1200)   # terminal velocity


def apply_friction(entity, dt: float, friction: float = 1200.0):
    """Horizontal ground friction when no input."""
    if entity.on_ground:
        entity.vx = approach_zero(entity.vx, friction * dt)


def approach_zero(value: float, delta: float) -> float:
    if abs(value) <= delta:
        return 0.0
    return value - sign(value) * delta
