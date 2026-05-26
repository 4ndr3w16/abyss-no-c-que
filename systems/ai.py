# ============================================================
# systems/ai.py — Enemy behaviour state machine
# ============================================================
from enum import Enum, auto
from utils.math_utils import distance, sign
from settings import *


class AIState(Enum):
    IDLE   = auto()
    CHASE  = auto()
    ATTACK = auto()
    HITSTUN = auto()
    DEAD   = auto()


class EnemyAI:
    """
    Drives one enemy's decision-making.
    Separated from rendering and physics — only writes to entity.intent.
    """

    def __init__(self, entity):
        self.entity  = entity
        self.state   = AIState.IDLE
        self._attack_cd = 0.0

    def update(self, dt: float, player):
        e = self.entity

        if not e.alive:
            self.state = AIState.DEAD
            return

        if e.hitstun_timer > 0:
            self.state = AIState.HITSTUN
            e.hitstun_timer -= dt
            e.intent_move = 0
            return

        dist = distance(e.rect.centerx, e.rect.centery,
                        player.rect.centerx, player.rect.centery)

        self._attack_cd = max(0.0, self._attack_cd - dt)

        if dist < ENEMY_ATTACK_RANGE and self._attack_cd <= 0:
            self.state = AIState.ATTACK
            e.intent_move = 0
            if not e.is_attacking():
                e.start_attack()
                self._attack_cd = ENEMY_ATTACK_COOLDOWN

        elif dist < ENEMY_CHASE_RANGE:
            self.state = AIState.CHASE
            dx = sign(player.rect.centerx - e.rect.centerx)
            e.intent_move = dx
            e.facing      = dx if dx != 0 else e.facing

        else:
            self.state = AIState.IDLE
            e.intent_move = 0
