# ============================================================
# core/game.py — Main game coordinator; owns all systems
# ============================================================
import pygame
import sys
from settings import *
from core.state  import GameState, StateMachine
from core.effects import EffectManager
from core.hud    import HUD
from core.timer  import Timer
from entities.player import Player
from world.dungeon   import Dungeon
from systems.combat  import resolve_attacks, apply_hit_events


class Camera:
    """Simple lerp-follow camera."""
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_rect: pygame.Rect, dt: float):
        tx = target_rect.centerx - SCREEN_WIDTH  // 2
        ty = target_rect.centery - SCREEN_HEIGHT // 2
        # Clamp to room bounds
        tx = max(0, min(tx, ROOM_W - SCREEN_WIDTH))
        ty = max(0, min(ty, ROOM_H - SCREEN_HEIGHT))
        # Lerp
        speed = 8.0
        self.x += (tx - self.x) * speed * dt
        self.y += (ty - self.y) * speed * dt


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen  = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock   = pygame.time.Clock()
        self.running = True

        self.sm      = StateMachine(GameState.MAIN_MENU)
        self.effects = EffectManager()
        self.hud     = HUD()
        self.camera  = Camera()

        self.effects.init_font()
        self.hud.init()

        self._trans_timer  = Timer(0.5)
        self._trans_dir    = None
        self._victory      = False

        self.player  = None
        self.dungeon = None

    # ── Lifecycle ─────────────────────────────────────────────
    def _start_new_run(self):
        self.dungeon = Dungeon()
        start_x = (ROOM_COLS // 2) * TILE_SIZE
        start_y = (ROOM_ROWS - 3) * TILE_SIZE
        self.player  = Player(start_x, start_y)
        self.camera  = Camera()
        self.effects = EffectManager()
        self.effects.init_font()
        self.sm.transition(GameState.PLAYING)

    # ── Events ────────────────────────────────────────────────
    def _handle_events(self) -> list:
        events = []
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.sm.current == GameState.PLAYING:
                        self.sm.transition(GameState.PAUSED)
                    elif self.sm.current == GameState.PAUSED:
                        self.sm.transition(GameState.PLAYING)
                    elif self.sm.current == GameState.CONTROLS:
                        self.sm.transition(GameState.MAIN_MENU)
                if ev.key == pygame.K_c:
                    if self.sm.current == GameState.MAIN_MENU:
                        self.sm.transition(GameState.CONTROLS)
                    elif self.sm.current == GameState.CONTROLS:
                        self.sm.transition(GameState.MAIN_MENU)
                if ev.key == pygame.K_RETURN:
                    if self.sm.current == GameState.MAIN_MENU:
                        self._start_new_run()
                    elif self.sm.current in (GameState.GAME_OVER, GameState.VICTORY):
                        self.sm.transition(GameState.MAIN_MENU)
            events.append(ev)
        return events

    # ── Update ────────────────────────────────────────────────
    def _update_playing(self, dt: float, keys, events):
        player  = self.player
        dungeon = self.dungeon
        room    = dungeon.current_room

        # Player
        player.update(dt, room.walls, keys, events)
        if not player.alive:
            self.sm.transition(GameState.GAME_OVER)
            return

        # Room
        room.update(dt, player)

        # ── Combat resolution ──────────────────────────────────
        living = [e for e in room.enemies if e.alive]

        # Player attacks enemies
        atk_events = resolve_attacks([player], living)
        for ev in atk_events:
            if ev.target.alive is False:
                self.effects.death_burst(ev.hx, ev.hy)
        apply_hit_events(atk_events, self.effects)

        # Falling attack (stomp)
        if player.is_falling_attack:
            stomp_hb = player.fall_attack_hitbox()
            if stomp_hb:
                for e in living:
                    if e.alive and stomp_hb.colliderect(e.rect):
                        if player.stomp(e):
                            self.effects.hit_sparks(stomp_hb.centerx,
                                                    stomp_hb.centery,
                                                    color=ACCENT2)
                            self.effects.death_burst(stomp_hb.centerx,
                                                     stomp_hb.centery,
                                                     color=(100, 200, 255))
                            self.player.combo.register_hit()

        # Enemies attack player
        enemy_events = resolve_attacks(living, [player])
        apply_hit_events(enemy_events, self.effects)

        # Effects
        self.effects.update(dt)

        # Dash trail
        if player.state in ("dash", "fall_atk"):
            self.effects.dash_trail(player.rect.centerx, player.rect.centery)

        # Camera
        self.camera.update(player.rect, dt)

        # Room transition check
        direction = dungeon.try_transition(player.rect)
        if direction:
            if direction in dungeon.current_room.connections:
                next_id = dungeon.current_room.connections[direction]
                dungeon.transition(direction, player)
                # Check victory (reached last room)
                if dungeon.current_room_id == len(dungeon.rooms) - 1:
                    self.sm.transition(GameState.VICTORY)

    # ── Draw ─────────────────────────────────────────────────
    def _draw_playing(self):
        room = self.dungeon.current_room
        cam  = self.camera

        room.draw(self.screen, cam.x, cam.y)
        self.effects.draw(self.screen, cam.x, cam.y)
        self.player.draw(self.screen, cam.x, cam.y)
        self.hud.draw(self.screen, self.player, self.dungeon, self.player.combo)

        if not room.cleared:
            # "Enemies remain" indicator
            font = pygame.font.SysFont("monospace", 14)
            remain = sum(1 for e in room.enemies if e.alive)
            txt = font.render(f"Enemies: {remain}", True, (200, 100, 100))
            self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, 52))

    # ── Main loop ─────────────────────────────────────────────
    def run(self):
        while self.running:
            dt   = self.clock.tick(FPS) / 1000.0
            dt   = min(dt, 0.05)   # cap spike frames
            keys = pygame.key.get_pressed()

            events = self._handle_events()
            if not self.running:
                break

            state = self.sm.current

            if state == GameState.MAIN_MENU:
                self.hud.draw_menu(self.screen)

            elif state == GameState.CONTROLS:
                self.hud.draw_controls(self.screen)

            elif state == GameState.PLAYING:
                self._update_playing(dt, keys, events)
                if self.sm.current == GameState.PLAYING:   # might have changed
                    self._draw_playing()

            elif state == GameState.PAUSED:
                self._draw_playing()
                self.hud.draw_overlay(self.screen, "PAUSED",
                                       "ESC to resume", ACCENT2)

            elif state == GameState.GAME_OVER:
                if self.player and self.dungeon:
                    self._draw_playing()
                self.hud.draw_overlay(self.screen, "YOU  DIED",
                                       "ENTER to return to menu",
                                       (220, 60, 60))

            elif state == GameState.VICTORY:
                if self.player and self.dungeon:
                    self._draw_playing()
                self.hud.draw_overlay(self.screen, "DUNGEON  CLEARED",
                                       "ENTER to return to menu",
                                       ACCENT2)

            pygame.display.flip()

        pygame.quit()
        sys.exit()
