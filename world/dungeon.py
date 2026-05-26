import pygame
import random
import math
from enum import Enum, auto
from settings import *
from entities.enemy import Enemy
from utils.math_utils import rect_overlap


class RoomType(Enum):
    EMPTY   = auto()
    COMBAT  = auto()
    ELITE   = auto()
    REWARD  = auto()
    START   = auto()
    BOSS    = auto()


TILE_EMPTY = 0
TILE_WALL  = 1
TILE_FLOOR = 2
TILE_DOOR_R = 3
TILE_DOOR_L = 4
TILE_PLATFM = 5


def _make_room_tiles(connections, door_positions):
    grid = [[TILE_EMPTY] * ROOM_COLS for _ in range(ROOM_ROWS)]

    for r in range(ROOM_ROWS):
        for c in range(ROOM_COLS):
            if r == 0 or r == ROOM_ROWS - 1 or c == 0 or c == ROOM_COLS - 1:
                grid[r][c] = TILE_WALL
            else:
                grid[r][c] = TILE_FLOOR

    # Doorways
    for direction, pos in door_positions.items():
        if direction == 'right':
            for dr in range(-1, 2):
                grid[pos + dr][ROOM_COLS - 1] = TILE_DOOR_R
        elif direction == 'left':
            for dr in range(-1, 2):
                grid[pos + dr][0] = TILE_DOOR_L

    ground_row = ROOM_ROWS - 3

    # Staircase platforms to each door + direct lift platform
    for direction, pos in door_positions.items():
        if direction == 'left':
            near_col = 2
        else:
            near_col = ROOM_COLS - 5

        # Direct vertical lift: platforms stacked at door column
        if pos < ground_row - 2:
            for step in range(pos + 2, ground_row + 1, 2):
                for dc in range(4):
                    gc = near_col + dc
                    if 0 < gc < ROOM_COLS - 1:
                        grid[step][gc] = TILE_PLATFM

        # One ground-level platform near the door to jump onto
        lift_row = ground_row - 1
        for dc in range(5):
            gc = near_col + dc
            if 0 < gc < ROOM_COLS - 1:
                grid[lift_row][gc] = TILE_PLATFM

    # Mid-air platforms across the room
    placed_rows = set()
    for _ in range(5):
        pr = random.randint(8, ground_row)
        if pr in placed_rows:
            continue
        placed_rows.add(pr)
        pc = random.randint(4, ROOM_COLS - 7)
        pw = random.randint(4, 7)
        for dc in range(pw):
            gc = pc + dc
            if 0 < gc < ROOM_COLS - 1 and grid[pr][gc] == TILE_FLOOR:
                grid[pr][gc] = TILE_PLATFM

    return grid


def _build_wall_rects(grid) -> list[pygame.Rect]:
    rects = []
    for r, row in enumerate(grid):
        for c, tile in enumerate(row):
            if tile in (TILE_WALL, TILE_PLATFM):
                rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE,
                                         TILE_SIZE, TILE_SIZE))
    return rects


PALTFORM_COLOR = (60, 50, 90)
PLATFORM_EDGE  = (90, 70, 130)


class Room:
    def __init__(self, room_id: int, rtype: RoomType,
                 connections: dict, door_positions: dict):
        self.id          = room_id
        self.type        = rtype
        self.connections = connections
        self.door_pos    = door_positions
        self.cleared     = (rtype == RoomType.EMPTY or rtype == RoomType.START)
        self.visited     = False

        self.grid = _make_room_tiles(connections, door_positions)
        self.walls: list[pygame.Rect] = _build_wall_rects(self.grid)
        self.enemies: list[Enemy] = []

    def spawn_enemies(self):
        if self.type == RoomType.START or self.type == RoomType.EMPTY:
            return
        if self.type == RoomType.ELITE:
            count = 1
            elite = True
        elif self.type == RoomType.COMBAT:
            count = random.randint(MIN_ENEMIES_COMBAT, MAX_ENEMIES_COMBAT)
            elite = False
        elif self.type == RoomType.REWARD:
            count = 1
            elite = False
        else:
            count = 0
            elite = False

        for _ in range(count):
            x = random.randint(4, ROOM_COLS - 5) * TILE_SIZE
            y = (ROOM_ROWS - 3) * TILE_SIZE
            self.enemies.append(Enemy(x, y, elite=elite))

    @property
    def surface(self) -> pygame.Surface:
        if hasattr(self, '_surface'):
            return self._surface
        surf = pygame.Surface((ROOM_W, ROOM_H))
        surf.fill(BG_COLOR)
        for r, row in enumerate(self.grid):
            for c, tile in enumerate(row):
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE,
                                   TILE_SIZE, TILE_SIZE)
                if tile == TILE_WALL:
                    pygame.draw.rect(surf, WALL_COLOR, rect)
                    pygame.draw.rect(surf, (40, 30, 60), rect, 1)
                elif tile == TILE_FLOOR:
                    pygame.draw.rect(surf, FLOOR_COLOR, rect)
                elif tile == TILE_PLATFM:
                    pygame.draw.rect(surf, PALTFORM_COLOR, rect)
                    pygame.draw.rect(surf, PLATFORM_EDGE, rect, 1)
                elif tile in (TILE_DOOR_R, TILE_DOOR_L):
                    pygame.draw.rect(surf, (60, 40, 80), rect)
                    pygame.draw.rect(surf, (120, 80, 160), rect, 2)
        self._surface = surf
        return surf

    def update(self, dt: float, player):
        from systems.ai import EnemyAI
        if not hasattr(self, '_ais'):
            self._ais = [EnemyAI(e) for e in self.enemies]
        for ai in self._ais:
            ai.update(dt, player)
        for e in self.enemies:
            e.update(dt, self.walls)
        if not self.cleared and all(not e.alive for e in self.enemies):
            self.cleared = True

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        surface.blit(self.surface, (-int(cam_x), -int(cam_y)))
        for e in self.enemies:
            e.draw(surface, cam_x, cam_y)
        if self.type == RoomType.REWARD and self.cleared:
            cx = ROOM_W // 2
            cy = ROOM_H // 2
            t = pygame.time.get_ticks() / 400
            pulse = int(5 * math.sin(t))
            pygame.draw.circle(surface, ACCENT2,
                               (cx - int(cam_x), cy - int(cam_y) + pulse), 12)

        # Door glow indicators
        t = pygame.time.get_ticks() / 600
        glow = int(25 + 20 * math.sin(t))
        for direction, pos in self.door_pos.items():
            c = (100 + glow, 60 + glow // 2, 140 + glow // 2)
            if direction == 'right':
                dx = ROOM_W - int(cam_x) - TILE_SIZE // 2
                dy = (pos + 0.5) * TILE_SIZE - int(cam_y)
            else:
                dx = -int(cam_x) + TILE_SIZE // 2
                dy = (pos + 0.5) * TILE_SIZE - int(cam_y)
            pygame.draw.circle(surface, c, (int(dx), int(dy)), 16, 3)


OPPOSITE = {'right': 'left', 'left': 'right'}
DIRS     = ['right', 'left']


class Dungeon:
    def __init__(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)
        self.rooms: dict[int, Room] = {}
        self.current_room_id = 0
        self._generate()

    def _generate(self):
        n = DUNGEON_ROOMS
        room_types = [RoomType.START]
        for i in range(1, n):
            if i == n - 1:
                room_types.append(RoomType.ELITE)
            elif i % 4 == 3:
                room_types.append(RoomType.REWARD)
            elif i % 5 == 0:
                room_types.append(RoomType.ELITE)
            else:
                room_types.append(RoomType.COMBAT)

        connections_map = [{} for _ in range(n)]
        door_pos_map    = [{} for _ in range(n)]

        for i in range(n - 1):
            connections_map[i]['right'] = i + 1
            connections_map[i + 1]['left'] = i

        for i, conn in enumerate(connections_map):
            for d in conn:
                door_pos_map[i][d] = random.randint(8, ROOM_ROWS - 5)

        for i, rtype in enumerate(room_types):
            room = Room(i, rtype, connections_map[i], door_pos_map[i])
            room.spawn_enemies()
            self.rooms[i] = room

        self.rooms[0].visited = True

    @property
    def current_room(self) -> Room:
        return self.rooms[self.current_room_id]

    def try_transition(self, player_rect: pygame.Rect):
        room = self.current_room
        if not room.cleared:
            return None

        for direction, pos in room.door_pos.items():
            door_h = 3 * TILE_SIZE
            margin = 8
            if direction == 'right':
                if player_rect.right >= ROOM_W - margin:
                    return 'right'
            elif direction == 'left':
                if player_rect.left <= margin:
                    return 'left'
        return None

    def transition(self, direction: str, player):
        next_id = self.current_room.connections[direction]
        self.current_room_id = next_id
        room = self.current_room
        room.visited = True

        margin = 3 * TILE_SIZE
        if direction == 'right':
            player.rect.x = margin
            player.rect.y = room.door_pos.get('left', ROOM_ROWS // 2) * TILE_SIZE
        elif direction == 'left':
            player.rect.x = ROOM_W - margin - player.rect.width
            player.rect.y = room.door_pos.get('right', ROOM_ROWS // 2) * TILE_SIZE

        player.vx = 0
        player.vy = 0
