import pygame
import math
import random
from settings import *


# ── Gothic palette extensions ──────────────────────────────
G_VOID       = ( 5,  5,  8)
G_ABYSS      = ( 9,  9, 15)
G_SHADOW     = (14, 14, 24)
G_DEEP       = (20, 20, 31)
G_SLATE      = (42, 42, 62)
G_BORDER     = (58, 58, 82)
G_DIM        = (90, 90,122)
G_FOG        = (136,136,170)
G_PALE       = (200,200,216)
G_LIGHT      = (232,224,240)
G_GOLD       = (201,168, 76)
G_GOLD_BR    = (232,200,106)
G_BLOOD      = (192, 57, 43)
G_CRIMSON    = (139, 26, 26)
G_ETHER      = (106, 58,192)
G_ETHER_BR   = (154,106,224)
G_ARCANE     = ( 74, 42,138)
G_JADE       = ( 42,138, 90)


class HUD:
    def __init__(self):
        self._font_lg  = None
        self._font_md  = None
        self._font_sm  = None
        self._rune_time = 0.0

    def init(self):
        self._font_lg = pygame.font.SysFont("monospace", 28, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 18, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 14)

    # ── Vignette overlay ──────────────────────────────────
    def draw_vignette(self, surface: pygame.Surface, alpha=180):
        w, h = surface.get_size()
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(max(w, h) // 2, 0, -1):
            a = int(max(0, 40 - 40 * i / (max(w, h) // 2)))
            if a == 0:
                continue
            color = (5, 5, 8, a)
            r = int(i * w / (max(w, h) / 2))
            if r <= 0:
                continue
            pygame.draw.ellipse(s, color,
                                (w//2 - r, h//2 - int(r * h / w),
                                 r * 2, int(r * h / w * 2)))
        surface.blit(s, (0, 0))

    def draw_noise(self, surface: pygame.Surface):
        s = pygame.Surface((surface.get_width(), surface.get_height()),
                           pygame.SRCALPHA)
        for _ in range(1200):
            x = random.randint(0, s.get_width() - 1)
            y = random.randint(0, s.get_height() - 1)
            v = random.randint(0, 30)
            s.set_at((x, y), (v, v, v, 10))
        surface.blit(s, (0, 0))

    # ── Menu ──────────────────────────────────────────────
    def draw_menu(self, surface: pygame.Surface):
        w, h = surface.get_size()
        surface.fill(G_VOID)

        self._rune_time += 0.016

        # Rune circles
        circles = [
            (min(w, h) * 0.7, G_ARCANE, 80),
            (min(w, h) * 0.5, G_CRIMSON, 55),
            (min(w, h) * 0.3, G_GOLD, 35),
        ]
        cx, cy = w // 2, h // 2
        for rad, color, period in circles:
            pts = 48
            angle_offset = self._rune_time * 2 * math.pi / period
            for i in range(pts):
                a = i * 2 * math.pi / pts + angle_offset
                px = cx + rad * math.cos(a)
                py = cy + rad * math.sin(a)
                alpha = 40 + 20 * math.sin(a * 3 + self._rune_time * 2)
                clr = (*color[:3], max(0, min(255, alpha)))
                pygame.draw.circle(surface, clr, (int(px), int(py)),
                                   max(1, int(2 + math.sin(a * 4 + self._rune_time * 3))))

        # Title
        title = self._font_lg.render("ABYSSAL  RIFT", True, G_GOLD)
        tw = title.get_width()
        # glow
        for dx, dy in [(2,0),(-2,0),(0,2),(0,-2)]:
            g = self._font_lg.render("ABYSSAL  RIFT", True, G_ARCANE)
            g.set_alpha(60)
            surface.blit(g, (w//2 - tw//2 + dx, h//2 - 80 + dy))
        surface.blit(title, (w // 2 - tw // 2, h // 2 - 80))

        # Subtitle
        sub = self._font_sm.render("descend, master, conquer", True, G_ETHER)
        surface.blit(sub, (w // 2 - sub.get_width() // 2, h // 2 - 40))

        # Press ENTER
        enter = self._font_md.render("Press  ENTER  to  begin", True, G_GOLD_BR)
        surface.blit(enter, (w // 2 - enter.get_width() // 2, h // 2 + 10))

        # Controls hint
        ctrl = self._font_sm.render("Press  C  for  controls", True, G_DIM)
        surface.blit(ctrl, (w // 2 - ctrl.get_width() // 2, h // 2 + 44))

        # Decorative line
        line_y = h // 2 + 70
        pygame.draw.line(surface, G_BORDER, (w // 2 - 100, line_y),
                         (w // 2 + 100, line_y))

        # Bottom tag
        tag = self._font_sm.render("where mastery is the only mercy", True, G_SLATE)
        surface.blit(tag, (w // 2 - tag.get_width() // 2, h - 40))

        self.draw_vignette(surface)
        self.draw_noise(surface)

    # ── Controls screen ───────────────────────────────────
    def draw_controls(self, surface: pygame.Surface):
        w, h = surface.get_size()
        surface.fill(G_VOID)

        self._rune_time += 0.016

        # Title
        title = self._font_lg.render("CONTROLS", True, G_GOLD)
        surface.blit(title, (w // 2 - title.get_width() // 2, 50))

        # Decorative line under title
        line_x = w // 2 - 120
        pygame.draw.line(surface, G_BORDER, (line_x, 90), (line_x + 240, 90))

        controls_data = [
            ("MOVEMENT", G_ETHER,
             [
                 ("WASD / Arrow Keys", "Move & jump"),
                 ("SHIFT + WASD", "Dash  (any direction)"),
                 ("SHIFT + DOWN (air)", "Falling attack  (stomp)"),
             ]),
            ("COMBAT", G_BLOOD,
             [
                 ("Z", "Attack"),
                 ("Z  (timed)", "Combo chain  (×4)"),
                 ("DOWN + SHIFT on enemy", "Stomp  (bounces up)"),
             ]),
            ("GAME", G_DIM,
             [
                 ("ENTER", "Confirm / Start"),
                 ("ESC", "Pause"),
                 ("C", "Toggle controls"),
             ]),
        ]

        y_start = 120
        col_w = w // 3
        for idx, (section_title, section_color, binds) in enumerate(controls_data):
            x_off = 60 + idx * col_w

            # Section title
            st = self._font_md.render(section_title, True, section_color)
            surface.blit(st, (x_off, y_start))

            # Divider
            pygame.draw.line(surface, G_SLATE,
                             (x_off, y_start + 24),
                             (x_off + col_w - 80, y_start + 24))

            for i, (key, action) in enumerate(binds):
                ky = y_start + 40 + i * 40

                key_surf = self._font_sm.render(key, True, G_LIGHT)
                surface.blit(key_surf, (x_off + 4, ky))

                act_surf = self._font_sm.render(action, True, G_FOG)
                surface.blit(act_surf, (x_off + 4, ky + 18))

        # Back hint
        back = self._font_sm.render("Press  C  or  ESC  to  return", True, G_DIM)
        surface.blit(back, (w // 2 - back.get_width() // 2, h - 50))

        self.draw_vignette(surface)
        self.draw_noise(surface)

    # ── In-game HUD ───────────────────────────────────────
    def draw(self, surface: pygame.Surface, player, dungeon, combo):
        w, h = surface.get_size()

        # HP bar
        bar_x, bar_y = 20, 20
        bar_w, bar_h = 220, 14
        hp_ratio = player.hp / player.max_hp
        filled = int(bar_w * hp_ratio)

        # Bar background
        pygame.draw.rect(surface, G_VOID, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, G_ABYSS, (bar_x, bar_y, bar_w, bar_h))
        if filled > 0:
            r = int(200 * (1 - hp_ratio))
            g = int(200 * hp_ratio)
            hp_color = (r, g, 50)
            pygame.draw.rect(surface, hp_color, (bar_x + 1, bar_y + 1, filled - 2, bar_h - 2))
        pygame.draw.rect(surface, G_SLATE, (bar_x, bar_y, bar_w, bar_h), 1)

        hp_txt = self._font_sm.render(f"HP  {player.hp}/{player.max_hp}", True, G_PALE)
        surface.blit(hp_txt, (bar_x, bar_y + bar_h + 4))

        # Dash indicator
        dash_ready = player._dash_cd.ready
        dash_color = G_ETHER_BR if dash_ready else G_SLATE
        pygame.draw.rect(surface, G_ABYSS, (bar_x, bar_y + bar_h + 24, 14, 14))
        pygame.draw.rect(surface, dash_color,
                         (bar_x + 1, bar_y + bar_h + 25, 12, 12))
        dash_lbl = self._font_sm.render("DASH", True, dash_color)
        surface.blit(dash_lbl, (bar_x + 20, bar_y + bar_h + 24))

        # Combo counter
        if combo.count >= 2:
            combo_txt = self._font_lg.render(f"COMBO  ×{combo.count}", True,
                                              G_GOLD_BR)
            # subtle glow
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                g = self._font_lg.render(f"COMBO  ×{combo.count}", True, G_ARCANE)
                g.set_alpha(50)
                surface.blit(g,
                    (w // 2 - combo_txt.get_width() // 2 + dx, 18 + dy))
            surface.blit(combo_txt,
                         (w // 2 - combo_txt.get_width() // 2, 18))

        # Room info
        room = dungeon.current_room
        rtype = room.type.name
        rid = room.id
        room_txt = self._font_sm.render(f"ROOM  {rid+1}/{len(dungeon.rooms)}  [{rtype}]",
                                         True, G_FOG)
        surface.blit(room_txt, (w - room_txt.get_width() - 16, 20))

        if room.cleared:
            clr = self._font_sm.render("CLEARED  →", True, G_ETHER_BR)
            surface.blit(clr, (w - clr.get_width() - 16, 40))

        # Minimap
        self._draw_minimap(surface, dungeon, w, h)

    def _draw_minimap(self, surface, dungeon, sw, sh):
        dot_size = 8
        spacing = 12
        n = len(dungeon.rooms)
        map_w = n * spacing
        ox = sw - map_w - 16
        oy = sh - 24

        for rid, room in dungeon.rooms.items():
            x = ox + rid * spacing
            if rid == dungeon.current_room_id:
                color = G_GOLD
            elif room.visited:
                color = G_FOG
            else:
                color = G_SLATE
            pygame.draw.rect(surface, color, (x, oy, dot_size, dot_size))

    # ── Overlays ──────────────────────────────────────────
    def draw_overlay(self, surface: pygame.Surface, text: str,
                     sub: str = "", color=G_PALE):
        w, h = surface.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((5, 5, 8, 200))
        surface.blit(overlay, (0, 0))

        main = self._font_lg.render(text, True, color)
        surface.blit(main, (w // 2 - main.get_width() // 2,
                             h // 2 - 30))
        if sub:
            sub_s = self._font_md.render(sub, True, G_FOG)
            surface.blit(sub_s, (w // 2 - sub_s.get_width() // 2,
                                  h // 2 + 16))
