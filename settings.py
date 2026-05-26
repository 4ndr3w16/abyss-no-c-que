# ============================================================
# settings.py — Global constants and configuration
# ============================================================

# Display
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "ABYSSAL RIFT"

# Tile & world
TILE_SIZE     = 48
ROOM_COLS     = 32
ROOM_ROWS     = 20
ROOM_W        = ROOM_COLS * TILE_SIZE   # pixels
ROOM_H        = ROOM_ROWS * TILE_SIZE

# Dungeon generation
DUNGEON_ROOMS        = 12
MIN_ENEMIES_COMBAT   = 3
MAX_ENEMIES_COMBAT   = 7
ELITE_HP_MULT        = 2.5
ELITE_DMG_MULT       = 1.8

# Physics / movement
GRAVITY          = 1800   # px/s²  (platformer axis: y grows down)
PLAYER_SPEED     = 240    # px/s
PLAYER_JUMP      = -850   # px/s  (initial velocity, negative = up)
DASH_HSPEED      = 680    # horizontal dash speed
DASH_VSPEED      = 600    # vertical dash speed
DASH_DURATION    = 0.14   # seconds
DASH_COOLDOWN    = 0.6
IFRAME_DURATION  = 0.22   # invulnerability window

# Falling attack
FALL_ATK_DAMAGE  = 30
FALL_ATK_BOUNCE  = -500  # upward velocity after stomping an enemy

# Combat — player
PLAYER_MAX_HP        = 100
PLAYER_ATK_DAMAGE    = 18
PLAYER_ATK_DURATION  = 0.18   # total animation length (s)
PLAYER_ATK_ACTIVE_START = 0.06  # hitbox appears at this frame-time
PLAYER_ATK_ACTIVE_END   = 0.15  # hitbox disappears
PLAYER_ATK_COOLDOWN  = 0.22
PLAYER_ATK_REACH     = 58     # hitbox half-width from player center
PLAYER_ATK_HEIGHT    = 40
COMBO_WINDOW         = 0.45   # time after hit to continue combo
MAX_COMBO            = 4      # hits before reset
COMBO_DAMAGE_MULT    = [1.0, 1.0, 1.2, 1.6]  # per hit in combo

# Combat — enemy
ENEMY_BASE_HP        = 40
ENEMY_BASE_DAMAGE    = 12
ENEMY_ATTACK_RANGE   = 52
ENEMY_CHASE_RANGE    = 320
ENEMY_ATTACK_COOLDOWN = 1.2
ENEMY_ATK_DURATION   = 0.4
ENEMY_ATK_ACTIVE_START = 0.15
ENEMY_ATK_ACTIVE_END   = 0.32
ENEMY_SPEED          = 110
ENEMY_HITSTUN        = 0.28

# Colors (palette: dark gothic)
BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)
BG_COLOR    = ( 12,   8,  18)
WALL_COLOR  = ( 28,  22,  42)
FLOOR_COLOR = ( 22,  18,  34)
ACCENT1     = (180,  60, 220)   # purple
ACCENT2     = ( 60, 200, 220)   # cyan
PLAYER_COLOR  = (200, 200, 255)
ENEMY_COLOR   = (220,  70,  70)
ELITE_COLOR   = (255, 140,  30)
HP_BAR_BG     = ( 50,  10,  10)
HP_BAR_FG     = (200,  30,  30)
PLAYER_HP_FG  = ( 60, 200, 100)
COMBO_COLOR   = (255, 220,  60)
DASH_COLOR    = ( 80, 140, 255)
HIT_FLASH     = (255, 255, 255)

# Layers / z-order (drawing order)
Z_FLOOR   = 0
Z_ENTITY  = 1
Z_EFFECT  = 2
Z_HUD     = 3
