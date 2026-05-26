# ============================================================
# core/effects.py — Lightweight particle / visual effect manager
# ============================================================
import pygame
import random
import math
from settings import *


class Particle:
    __slots__ = ('x','y','vx','vy','life','max_life','radius','color','gravity')

    def __init__(self, x, y, vx, vy, life, radius, color, gravity=0):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.life = self.max_life = life
        self.radius = radius
        self.color = color
        self.gravity = gravity

    def update(self, dt):
        self.vy += self.gravity * dt
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface, cam_x, cam_y):
        alpha = self.life / self.max_life
        r = max(1, int(self.radius * alpha))
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        c = tuple(int(ch * alpha) for ch in self.color)
        pygame.draw.circle(surface, c, (sx, sy), r)


class HitNumber:
    """Floating damage numbers."""
    __slots__ = ('x','y','value','life','combo','color')

    def __init__(self, x, y, value, combo=1):
        self.x, self.y = float(x), float(y)
        self.value = value
        self.life = 0.9
        self.combo = combo
        self.color = COMBO_COLOR if combo >= 3 else WHITE

    def update(self, dt):
        self.y  -= 60 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface, font, cam_x, cam_y):
        alpha = min(1.0, self.life / 0.4)
        size  = 16 + min(self.combo, 4) * 4
        txt   = f"{self.value}"
        if self.combo >= 2:
            txt = f"x{self.combo} {self.value}"
        color = tuple(int(c * alpha) for c in self.color)
        surf  = font.render(txt, True, color)
        sx = int(self.x - cam_x) - surf.get_width() // 2
        sy = int(self.y - cam_y)
        surface.blit(surf, (sx, sy))


class EffectManager:
    def __init__(self):
        self._particles: list[Particle] = []
        self._numbers:   list[HitNumber] = []
        self._font = None

    def init_font(self):
        self._font = pygame.font.SysFont("monospace", 18, bold=True)

    # ── Spawners ──────────────────────────────────────────────
    def hit_sparks(self, x, y, count=8, color=ACCENT1):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 260)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life  = random.uniform(0.12, 0.30)
            r     = random.uniform(2, 5)
            self._particles.append(Particle(x, y, vx, vy, life, r, color, gravity=400))

    def dash_trail(self, x, y, color=DASH_COLOR):
        for _ in range(4):
            vx = random.uniform(-30, 30)
            vy = random.uniform(-30, 30)
            life = random.uniform(0.08, 0.18)
            r    = random.uniform(3, 7)
            self._particles.append(Particle(x, y, vx, vy, life, r, color))

    def death_burst(self, x, y, color=ENEMY_COLOR):
        self.hit_sparks(x, y, count=20, color=color)

    def damage_number(self, x, y, value, combo=1):
        self._numbers.append(HitNumber(x, y, value, combo))

    # ── Update / Draw ─────────────────────────────────────────
    def update(self, dt):
        self._particles = [p for p in self._particles if p.update(dt)]
        self._numbers   = [n for n in self._numbers   if n.update(dt)]

    def draw(self, surface, cam_x, cam_y):
        for p in self._particles:
            p.draw(surface, cam_x, cam_y)
        if self._font:
            for n in self._numbers:
                n.draw(surface, self._font, cam_x, cam_y)
