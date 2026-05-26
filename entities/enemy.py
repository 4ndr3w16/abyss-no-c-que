# ============================================================
# entities/enemy.py — Base enemy and Elite variant
# ============================================================
import pygame
from settings import *
from systems.combat import AttackState
from systems.movement import move_and_collide, apply_gravity, apply_friction
from utils.math_utils import clamp


class Enemy:
    def __init__(self, x: float, y: float, elite: bool = False):
        w, h = 30, 40
        self.rect      = pygame.Rect(int(x), int(y), w, h)
        self.vx        = 0.0
        self.vy        = 0.0
        self.on_ground = False
        self.facing    = -1
        self.elite     = elite
        self.alive     = True

        hp_mult  = ELITE_HP_MULT  if elite else 1.0
        dmg_mult = ELITE_DMG_MULT if elite else 1.0
        self.max_hp = int(ENEMY_BASE_HP  * hp_mult)
        self.hp     = self.max_hp
        self.damage = int(ENEMY_BASE_DAMAGE * dmg_mult)

        # Intent set by AI
        self.intent_move  = 0      # -1 / 0 / +1
        self.hitstun_timer = 0.0

        # Attack
        self.current_attack: AttackState | None = None
        self._atk_anim_t = 0.0

        # Visual
        self.flash_t = 0.0

    # ── Combat interface ──────────────────────────────────────
    def is_attacking(self) -> bool:
        return self.current_attack is not None

    def start_attack(self):
        self.current_attack = AttackState(
            duration      = ENEMY_ATK_DURATION,
            active_start  = ENEMY_ATK_ACTIVE_START,
            active_end    = ENEMY_ATK_ACTIVE_END,
            damage        = self.damage,
            reach         = ENEMY_ATTACK_RANGE,
            height        = 36,
            facing        = self.facing,
            origin_getter = lambda: (self.rect.centerx, self.rect.centery)
        )
        self._atk_anim_t = 0.0

    def take_damage(self, amount: int):
        if not self.alive:
            return
        self.hp = max(0, self.hp - amount)
        self.flash_t = 0.12
        self.hitstun_timer = ENEMY_HITSTUN
        if self.hp <= 0:
            self.alive = False

    # ── Update ────────────────────────────────────────────────
    def update(self, dt: float, walls: list[pygame.Rect]):
        if not self.alive:
            return

        self.flash_t = max(0.0, self.flash_t - dt)

        # Attack lifecycle
        if self.current_attack:
            if not self.current_attack.update(dt):
                self.current_attack = None

        # Apply movement intent
        if self.hitstun_timer <= 0 and self.intent_move != 0:
            self.vx = self.intent_move * ENEMY_SPEED
        elif self.hitstun_timer <= 0:
            self.vx = 0.0

        apply_gravity(self, dt)
        apply_friction(self, dt)
        move_and_collide(self, walls, dt)

    # ── Draw ──────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        if not self.alive:
            return
        sx = self.rect.x - int(cam_x)
        sy = self.rect.y - int(cam_y)

        base_color = ELITE_COLOR if self.elite else ENEMY_COLOR
        color = HIT_FLASH if self.flash_t > 0 else base_color

        pygame.draw.rect(surface, color, (sx, sy, self.rect.width, self.rect.height))

        # Eyes
        eye_x = sx + self.rect.width // 2 + self.facing * 5
        pygame.draw.circle(surface, (255, 220, 50), (eye_x, sy + 8), 4)

        # Elite crown indicator
        if self.elite:
            pts = [(sx + self.rect.width//2 - 8, sy - 2),
                   (sx + self.rect.width//2,     sy - 10),
                   (sx + self.rect.width//2 + 8, sy - 2)]
            pygame.draw.polygon(surface, ELITE_COLOR, pts)

        # HP bar
        bar_w = self.rect.width
        bar_h = 4
        filled = int(bar_w * (self.hp / self.max_hp))
        pygame.draw.rect(surface, HP_BAR_BG, (sx, sy - 8, bar_w, bar_h))
        if filled > 0:
            pygame.draw.rect(surface, HP_BAR_FG, (sx, sy - 8, filled, bar_h))

        # Active hitbox
        if self.current_attack and self.current_attack.in_active_window:
            hb = self.current_attack.get_hitbox()
            s = pygame.Surface((hb.width, hb.height), pygame.SRCALPHA)
            s.fill((255, 80, 80, 50))
            surface.blit(s, (hb.x - int(cam_x), hb.y - int(cam_y)))
