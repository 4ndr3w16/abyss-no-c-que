import pygame
from settings import *
from core.timer import CooldownTimer, Timer
from systems.combat import AttackState, ComboTracker
from systems.movement import move_and_collide, apply_gravity, apply_friction
from utils.math_utils import clamp, sign


class PlayerState:
    IDLE     = "idle"
    RUN      = "run"
    JUMP     = "jump"
    FALL     = "fall"
    DASH     = "dash"
    ATTACK   = "attack"
    FALL_ATK = "fall_atk"
    HITSTUN  = "hitstun"
    DEAD     = "dead"


class Player:
    def __init__(self, x: float, y: float):
        w, h = 28, 44
        self.rect      = pygame.Rect(int(x), int(y), w, h)
        self.vx        = 0.0
        self.vy        = 0.0
        self.on_ground = False
        self.facing    = 1
        self.state     = PlayerState.IDLE

        self.max_hp = PLAYER_MAX_HP
        self.hp     = self.max_hp
        self.alive  = True

        self._dash_cd   = CooldownTimer(DASH_COOLDOWN)
        self._dash_t    = Timer(DASH_DURATION)
        self._atk_cd    = CooldownTimer(PLAYER_ATK_COOLDOWN)
        self._iframe_t  = Timer(IFRAME_DURATION)
        self._hitstun_t = Timer(0)

        self.current_attack: AttackState | None = None
        self.combo = ComboTracker()

        # Falling attack (stomp)
        self._fall_atk_active = False
        self._stomped: set = set()

        self.flash_t = 0.0

    # ── Properties ────────────────────────────────────────────
    @property
    def invulnerable(self) -> bool:
        return self._iframe_t.active

    @property
    def center(self):
        return self.rect.centerx, self.rect.centery

    @property
    def is_falling_attack(self) -> bool:
        return self._fall_atk_active

    def fall_attack_hitbox(self) -> pygame.Rect | None:
        if not self._fall_atk_active:
            return None
        return pygame.Rect(self.rect.x - 8, self.rect.bottom,
                           self.rect.width + 16, 16)

    def stomp(self, enemy):
        if enemy in self._stomped or not enemy.alive:
            return False
        self._stomped.add(enemy)
        enemy.take_damage(FALL_ATK_DAMAGE)
        self.vy = FALL_ATK_BOUNCE
        return True

    # ── Input handling ────────────────────────────────────────
    def handle_input(self, keys, events):
        if self.state in (PlayerState.HITSTUN, PlayerState.DEAD):
            return

        # Dash (horizontal or vertical)
        if self.state not in (PlayerState.DASH, PlayerState.FALL_ATK):
            if keys[pygame.K_LSHIFT] and self._dash_cd.ready:
                dx = 0
                dy = 0
                if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
                if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
                if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1

                if dy > 0 and not self.on_ground:
                    self._start_fall_attack()
                    return
                elif dx != 0 or dy != 0:
                    self._start_dash(dx, dy)
                    return
                elif self.facing != 0:
                    self._start_dash(self.facing, 0)
                    return

        # Attack
        if self.state != PlayerState.DASH:
            for ev in events:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_z:
                    if self._atk_cd.ready and self.state != PlayerState.ATTACK:
                        self._start_attack()
                        break

        # Movement
        if self.state not in (PlayerState.DASH, PlayerState.ATTACK,
                               PlayerState.FALL_ATK):
            move_x = 0
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]: move_x -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_x += 1

            if move_x != 0:
                self.facing = move_x
                self.vx = move_x * PLAYER_SPEED
            else:
                self.vx = 0.0

            if (keys[pygame.K_UP] or keys[pygame.K_w] or
                    keys[pygame.K_SPACE]) and self.on_ground:
                self.vy = PLAYER_JUMP

    # ── Actions ───────────────────────────────────────────────
    def _start_dash(self, dx: int, dy: int):
        self.state = PlayerState.DASH
        self._dash_cd.start()
        self._dash_t.start()
        self._iframe_t.start(IFRAME_DURATION)
        mag = max(abs(dx), abs(dy))
        if mag == 0:
            return
        self.vx = (dx / mag) * DASH_HSPEED
        self.vy = (dy / mag) * DASH_VSPEED

    def _start_fall_attack(self):
        self.state = PlayerState.FALL_ATK
        self._fall_atk_active = True
        self._stomped.clear()
        self._dash_cd.start()
        self._iframe_t.start(IFRAME_DURATION * 0.6)
        self.vx = 0
        self.vy = DASH_VSPEED * 1.2

    def _start_attack(self):
        self.state = PlayerState.ATTACK
        self._atk_cd.start()
        self.current_attack = AttackState(
            duration     = PLAYER_ATK_DURATION,
            active_start = PLAYER_ATK_ACTIVE_START,
            active_end   = PLAYER_ATK_ACTIVE_END,
            damage       = PLAYER_ATK_DAMAGE,
            reach        = PLAYER_ATK_REACH,
            height       = PLAYER_ATK_HEIGHT,
            facing       = self.facing,
            origin_getter= lambda: (self.rect.centerx, self.rect.centery)
        )

    def take_damage(self, amount: int):
        if self.invulnerable or not self.alive:
            return
        self.hp = max(0, self.hp - amount)
        self.flash_t = 0.15
        if self.hp == 0:
            self.alive = False
            self.state = PlayerState.DEAD
            return
        self._iframe_t.start(IFRAME_DURATION)
        self._hitstun_t.start(0.2)
        self.state = PlayerState.HITSTUN
        self.vx = -self.facing * 180
        self.vy = -250

    # ── Update ────────────────────────────────────────────────
    def update(self, dt: float, walls: list[pygame.Rect], keys, events):
        self._dash_cd.update(dt)
        self._atk_cd.update(dt)
        self._dash_t.update(dt)
        self._iframe_t.update(dt)
        self._hitstun_t.update(dt)
        self.combo.update(dt)
        self.flash_t = max(0.0, self.flash_t - dt)

        # Attack lifecycle
        if self.current_attack:
            if not self.current_attack.update(dt):
                self.current_attack = None
                if self.state == PlayerState.ATTACK:
                    self.state = PlayerState.IDLE

        # Dash end
        if self.state == PlayerState.DASH and self._dash_t.done:
            self.state = PlayerState.IDLE
            self.vx *= 0.3
            self.vy = 0

        # Falling attack: end on ground
        if self.state == PlayerState.FALL_ATK:
            if self.on_ground:
                self._fall_atk_active = False
                self._stomped.clear()
                self.state = PlayerState.IDLE

        # Hitstun end
        if self.state == PlayerState.HITSTUN and self._hitstun_t.done:
            self.state = PlayerState.IDLE

        # Input
        self.handle_input(keys, events)

        # Physics
        if self.state not in (PlayerState.DASH, PlayerState.FALL_ATK):
            apply_gravity(self, dt)
            apply_friction(self, dt)

        move_and_collide(self, walls, dt)

        # Visual state (does not override action states)
        if self.state not in (PlayerState.ATTACK, PlayerState.DASH,
                               PlayerState.FALL_ATK,
                               PlayerState.HITSTUN, PlayerState.DEAD):
            if not self.on_ground:
                self.state = PlayerState.JUMP if self.vy < 0 else PlayerState.FALL
            elif abs(self.vx) > 10:
                self.state = PlayerState.RUN
            else:
                self.state = PlayerState.IDLE

    # ── Draw ─────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        sx = self.rect.x - int(cam_x)
        sy = self.rect.y - int(cam_y)

        if self.invulnerable and int(pygame.time.get_ticks() / 50) % 2 == 0:
            return

        color = HIT_FLASH if self.flash_t > 0 else PLAYER_COLOR

        # Falling attack glow
        if self.state == PlayerState.FALL_ATK:
            glow = pygame.Surface((self.rect.width + 16, self.rect.height + 16),
                                  pygame.SRCALPHA)
            glow.fill((*ACCENT2, 40))
            surface.blit(glow, (sx - 8, sy - 8))

        # Body
        pygame.draw.rect(surface, color, (sx, sy, self.rect.width, self.rect.height))

        # Eyes
        eye_x = sx + (self.rect.width // 2) + self.facing * 6
        eye_y = sy + 10
        pygame.draw.circle(surface, ACCENT2, (eye_x, eye_y), 4)

        # Dash glow
        if self.state == PlayerState.DASH:
            glow = pygame.Surface((self.rect.width + 12, self.rect.height + 12),
                                  pygame.SRCALPHA)
            pygame.draw.rect(glow, (*DASH_COLOR, 60), glow.get_rect(), border_radius=4)
            surface.blit(glow, (sx - 6, sy - 6))

        # Falling attack hitbox
        if self._fall_atk_active:
            hb = self.fall_attack_hitbox()
            if hb:
                s = pygame.Surface((hb.width, hb.height), pygame.SRCALPHA)
                s.fill((*ACCENT2, 80))
                surface.blit(s, (hb.x - int(cam_x), hb.y - int(cam_y)))

        # Attack hitbox
        if self.current_attack and self.current_attack.in_active_window:
            hbox = self.current_attack.get_hitbox()
            hx = hbox.x - int(cam_x)
            hy = hbox.y - int(cam_y)
            s = pygame.Surface((hbox.width, hbox.height), pygame.SRCALPHA)
            s.fill((*ACCENT1, 55))
            surface.blit(s, (hx, hy))
